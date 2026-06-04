import io
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd


REQUIRED_COLUMNS = [
    "record_id",
    "reporting_period",
    "legal_entity",
    "account_code",
    "account_name",
    "cost_center",
    "product",
    "currency",
    "oracle_amount",
    "frp_amount",
    "source_system",
]


@dataclass
class ProcessOutput:
    reconciliation_df: pd.DataFrame
    break_analysis_df: pd.DataFrame
    po_action_plan_df: pd.DataFrame
    prioritized_backlog_df: pd.DataFrame
    executive_summary_df: pd.DataFrame
    metrics: Dict[str, str]
    analytics_period_df: pd.DataFrame
    analytics_break_df: pd.DataFrame


def validate_input_columns(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    return len(missing) == 0, missing


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _classify_break(row: pd.Series) -> str:
    if row["oracle_amount"] > 0 and row["frp_amount"] == 0:
        return "Missing in FRP"
    if row["oracle_amount"] == 0 and row["frp_amount"] > 0:
        return "Orphan FRP Record"
    if row["oracle_amount"] != row["frp_amount"]:
        return "Amount Break"
    return "Matched"


def _severity_from_row(row: pd.Series) -> str:
    if row["break_type"] == "Matched":
        return "None"
    if row["break_type"] in {"Missing in FRP", "Orphan FRP Record"}:
        return "High"
    difference = abs(row["difference"])
    if difference >= 10000:
        return "High"
    if difference >= 5000:
        return "Medium"
    return "Low"


def _build_reconciliation(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    output["oracle_amount"] = _to_number(output["oracle_amount"])
    output["frp_amount"] = _to_number(output["frp_amount"])
    output["difference"] = output["oracle_amount"] - output["frp_amount"]
    output["break_type"] = output.apply(_classify_break, axis=1)
    output["severity"] = output.apply(_severity_from_row, axis=1)
    output["status"] = output["break_type"].apply(lambda value: "Passed" if value == "Matched" else "Open")
    output["recon_id"] = [f"REC-{index:03d}" for index in range(1, len(output) + 1)]

    return output[
        [
            "recon_id",
            "record_id",
            "reporting_period",
            "legal_entity",
            "account_code",
            "account_name",
            "cost_center",
            "product",
            "currency",
            "oracle_amount",
            "frp_amount",
            "difference",
            "break_type",
            "severity",
            "status",
        ]
    ]


def _owner_for_break(break_type: str) -> str:
    owners = {
        "Missing in FRP": "Data Team",
        "Orphan FRP Record": "Control Team",
        "Amount Break": "Finance Team",
    }
    return owners.get(break_type, "N/A")


def _action_for_break(break_type: str) -> str:
    actions = {
        "Missing in FRP": "Check load pipeline and missing source mapping.",
        "Orphan FRP Record": "Validate lineage and remove invalid target rows.",
        "Amount Break": "Review mapping/transformation and re-run reconciliation.",
    }
    return actions.get(break_type, "No action needed.")


def _build_break_analysis(reconciliation_df: pd.DataFrame) -> pd.DataFrame:
    breaks = reconciliation_df[reconciliation_df["break_type"] != "Matched"].copy()
    if breaks.empty:
        return pd.DataFrame(
            columns=[
                "recon_id",
                "break_type",
                "recommended_owner",
                "recommended_action",
                "business_impact",
            ]
        )
    breaks["recommended_owner"] = breaks["break_type"].apply(_owner_for_break)
    breaks["recommended_action"] = breaks["break_type"].apply(_action_for_break)
    breaks["business_impact"] = breaks["severity"].map(
        {
            "High": "Can impact monthly/quarterly reporting confidence.",
            "Medium": "Can impact reporting quality if delayed.",
            "Low": "Low impact, monitor and close.",
        }
    )
    return breaks[["recon_id", "break_type", "recommended_owner", "recommended_action", "business_impact"]]


def _build_po_action_plan(break_analysis_df: pd.DataFrame, reconciliation_df: pd.DataFrame) -> pd.DataFrame:
    if break_analysis_df.empty:
        return pd.DataFrame(
            columns=["action_id", "recon_id", "action_title", "priority", "owner", "next_step"]
        )
    lookup = reconciliation_df.set_index("recon_id").to_dict(orient="index")
    rows = []
    for index, row in break_analysis_df.reset_index(drop=True).iterrows():
        recon = lookup.get(row["recon_id"], {})
        priority = "High" if recon.get("severity") == "High" else "Medium"
        rows.append(
            {
                "action_id": f"ACT-{index + 1:03d}",
                "recon_id": row["recon_id"],
                "action_title": f"Fix {row['break_type']} for {recon.get('account_name', 'account')}",
                "priority": priority,
                "owner": row["recommended_owner"],
                "next_step": row["recommended_action"],
            }
        )
    return pd.DataFrame(rows)


def _build_prioritized_backlog(po_action_plan_df: pd.DataFrame) -> pd.DataFrame:
    if po_action_plan_df.empty:
        return pd.DataFrame(columns=["backlog_id", "action_id", "feature", "priority", "owner", "rank"])
    backlog = po_action_plan_df.copy()
    backlog["rank_value"] = backlog["priority"].map({"High": 1, "Medium": 2, "Low": 3})
    backlog = backlog.sort_values(["rank_value", "action_id"]).reset_index(drop=True)
    backlog["rank"] = backlog.index + 1
    backlog["backlog_id"] = [f"BL-{index:03d}" for index in range(1, len(backlog) + 1)]
    backlog["feature"] = backlog["action_title"]
    return backlog[["backlog_id", "action_id", "feature", "priority", "owner", "rank"]]


def _build_executive_summary(reconciliation_df: pd.DataFrame, po_action_plan_df: pd.DataFrame) -> pd.DataFrame:
    total_records = len(reconciliation_df)
    open_breaks = int((reconciliation_df["status"] == "Open").sum())
    high_breaks = int((reconciliation_df["severity"] == "High").sum())
    status = "Green" if open_breaks == 0 else ("Amber" if high_breaks < 3 else "Red")
    return pd.DataFrame(
        [
            {"section": "Overall Status", "generated_summary": status},
            {"section": "Records Reviewed", "generated_summary": str(total_records)},
            {"section": "Open Issues", "generated_summary": str(open_breaks)},
            {"section": "High Severity Issues", "generated_summary": str(high_breaks)},
            {
                "section": "PO Actions Created",
                "generated_summary": str(len(po_action_plan_df)),
            },
            {
                "section": "Recommendation",
                "generated_summary": "Close high severity items first, then medium items in backlog order.",
            },
        ]
    )


def _build_metrics(reconciliation_df: pd.DataFrame, po_action_plan_df: pd.DataFrame) -> Dict[str, str]:
    return {
        "Total Records": str(len(reconciliation_df)),
        "Matched Records": str((reconciliation_df["break_type"] == "Matched").sum()),
        "Open Breaks": str((reconciliation_df["status"] == "Open").sum()),
        "High Severity": str((reconciliation_df["severity"] == "High").sum()),
        "Actions Created": str(len(po_action_plan_df)),
    }


def _build_analytics(reconciliation_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    period_df = (
        reconciliation_df.assign(abs_difference=lambda frame: frame["difference"].abs())
        .groupby("reporting_period", as_index=False)
        .agg(total_difference=("abs_difference", "sum"), open_breaks=("status", lambda x: (x == "Open").sum()))
    )
    break_df = (
        reconciliation_df[reconciliation_df["break_type"] != "Matched"]
        .assign(abs_difference=lambda frame: frame["difference"].abs())
        .groupby("break_type", as_index=False)
        .agg(count=("recon_id", "count"), total_difference=("abs_difference", "sum"))
    )
    return period_df, break_df


def process_input_data(uploaded_df: pd.DataFrame) -> ProcessOutput:
    reconciliation_df = _build_reconciliation(uploaded_df)
    break_analysis_df = _build_break_analysis(reconciliation_df)
    po_action_plan_df = _build_po_action_plan(break_analysis_df, reconciliation_df)
    prioritized_backlog_df = _build_prioritized_backlog(po_action_plan_df)
    executive_summary_df = _build_executive_summary(reconciliation_df, po_action_plan_df)
    metrics = _build_metrics(reconciliation_df, po_action_plan_df)
    analytics_period_df, analytics_break_df = _build_analytics(reconciliation_df)
    return ProcessOutput(
        reconciliation_df=reconciliation_df,
        break_analysis_df=break_analysis_df,
        po_action_plan_df=po_action_plan_df,
        prioritized_backlog_df=prioritized_backlog_df,
        executive_summary_df=executive_summary_df,
        metrics=metrics,
        analytics_period_df=analytics_period_df,
        analytics_break_df=analytics_break_df,
    )


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")
