import random

import pandas as pd
import plotly.express as px
import streamlit as st

from processor import process_input_data, to_csv_bytes, validate_input_columns


st.set_page_config(page_title="AI Reconciliation Command Center", page_icon="📊", layout="wide")

st.markdown("# AI Reconciliation Command Center")
st.caption("Simple demo: generates 15 random rows and gives clear outputs for decision-making.")
st.info("Demo note: the sample rows are fake and generated inside the app.")

with st.expander("Required input columns"):
    st.code(
        "record_id, reporting_period, legal_entity, account_code, account_name, cost_center, "
        "product, currency, oracle_amount, frp_amount, source_system"
    )

LEGAL_ENTITIES = [
    "Northstar Health LLC",
    "Aurora Retail Inc",
    "Pioneer Logistics Group",
    "Summit Energy Partners",
    "Blue Peak Manufacturing",
    "Harbor Tech Services",
    "Evergreen Education Co",
    "Metro Media Studios",
]

ACCOUNT_OPTIONS = [
    ("4001", "Subscription Revenue", "Digital Services"),
    ("5102", "Cloud Hosting Expense", "Technology"),
    ("6205", "Regional Payroll", "Operations"),
    ("7301", "Freight and Delivery", "Supply Chain"),
    ("8404", "Facility Lease", "Corporate Services"),
    ("9108", "Customer Support Fees", "Customer Operations"),
    ("2250", "Clinical Supplies", "Healthcare Operations"),
    ("3360", "Field Maintenance", "Infrastructure"),
]

SOURCE_SYSTEMS = [
    "NetSuite",
    "Oracle ERP",
    "SAP S/4HANA",
    "Workday",
    "Salesforce",
    "Coupa",
    "ServiceNow",
    "Shopify",
]


def build_sample_input(row_count: int = 15) -> pd.DataFrame:
    random.seed()
    rows = []
    break_modes = ["matched", "amount_break", "missing_in_frp", "orphan_frp"]
    periods = pd.date_range("2026-01-01", periods=6, freq="MS").strftime("%Y-%m").tolist()
    currencies = ["USD", "EUR", "GBP", "CAD"]

    for index in range(row_count):
        account_code, account_name, product = random.choice(ACCOUNT_OPTIONS)
        legal_entity = random.choice(LEGAL_ENTITIES)
        source_system = random.choice(SOURCE_SYSTEMS)
        break_mode = break_modes[index % len(break_modes)]
        base_amount = random.randint(2_500, 45_000)

        if break_mode == "matched":
            oracle_amount = base_amount
            frp_amount = base_amount
        elif break_mode == "amount_break":
            oracle_amount = base_amount
            frp_amount = max(0, base_amount - random.randint(250, 6_000))
            if frp_amount == oracle_amount:
                frp_amount = max(0, base_amount - 1)
        elif break_mode == "missing_in_frp":
            oracle_amount = base_amount
            frp_amount = 0
        else:
            oracle_amount = 0
            frp_amount = base_amount

        rows.append(
            {
                "record_id": f"R-{index + 1:03d}",
                "reporting_period": random.choice(periods),
                "legal_entity": legal_entity,
                "account_code": account_code,
                "account_name": account_name,
                "cost_center": f"CC-{random.randint(100, 999)}",
                "product": product,
                "currency": random.choice(currencies),
                "oracle_amount": oracle_amount,
                "frp_amount": frp_amount,
                "source_system": source_system,
            }
        )

    return pd.DataFrame(rows)


if "input_df" not in st.session_state:
    st.session_state.input_df = build_sample_input()

col_refresh, col_note = st.columns([1, 3])
with col_refresh:
    if st.button("Generate new 15 rows"):
        st.session_state.input_df = build_sample_input()
with col_note:
    st.write("The app uses generated rows now, so no file upload is needed.")

input_df = st.session_state.input_df.copy()
is_valid, missing_columns = validate_input_columns(input_df)
if not is_valid:
    st.error(f"Missing required columns: {', '.join(missing_columns)}")
    st.stop()

with st.expander("Generated input rows"):
    st.dataframe(input_df, use_container_width=True, height=320)

output = process_input_data(input_df)

st.subheader("Top Summary")
metric_columns = st.columns(len(output.metrics))
for index, (label, value) in enumerate(output.metrics.items()):
    metric_columns[index].metric(label, value)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Reconciliation Results",
        "Break Analysis",
        "PO Action Plan",
        "Prioritized Backlog",
        "Executive Summary",
        "Analytics",
    ]
)

with tab1:
    st.dataframe(output.reconciliation_df, use_container_width=True, height=360)
    col_a, col_b = st.columns(2)
    with col_a:
        status_chart = px.pie(
            output.reconciliation_df,
            names="status",
            title="Passed vs Open",
            hole=0.55,
        )
        st.plotly_chart(status_chart, use_container_width=True)
    with col_b:
        severity_order = ["High", "Medium", "Low", "None"]
        severity_chart = px.histogram(
            output.reconciliation_df,
            x="severity",
            category_orders={"severity": severity_order},
            color="severity",
            title="Severity Distribution",
        )
        st.plotly_chart(severity_chart, use_container_width=True)

with tab2:
    st.dataframe(output.break_analysis_df, use_container_width=True, height=320)
    if not output.break_analysis_df.empty:
        owner_mix = output.break_analysis_df["recommended_owner"].value_counts().reset_index()
        owner_mix.columns = ["recommended_owner", "count"]
        owner_chart = px.bar(owner_mix, x="recommended_owner", y="count", title="Breaks by Owner")
        st.plotly_chart(owner_chart, use_container_width=True)

with tab3:
    st.dataframe(output.po_action_plan_df, use_container_width=True, height=320)
    if not output.po_action_plan_df.empty:
        priority_mix = output.po_action_plan_df["priority"].value_counts().reset_index()
        priority_mix.columns = ["priority", "count"]
        priority_chart = px.bar(priority_mix, x="priority", y="count", color="priority", title="PO Actions by Priority")
        st.plotly_chart(priority_chart, use_container_width=True)

with tab4:
    st.dataframe(output.prioritized_backlog_df, use_container_width=True, height=320)
    if not output.prioritized_backlog_df.empty:
        rank_chart = px.bar(
            output.prioritized_backlog_df.sort_values("rank").head(10),
            x="backlog_id",
            y="rank",
            color="priority",
            title="Top 10 Backlog Items by Rank",
        )
        st.plotly_chart(rank_chart, use_container_width=True)

with tab5:
    st.dataframe(output.executive_summary_df, use_container_width=True, height=280)

with tab6:
    if not output.analytics_break_df.empty:
        chart1 = px.bar(output.analytics_break_df, x="break_type", y="count", title="Break Count by Type")
        st.plotly_chart(chart1, use_container_width=True)
        chart2 = px.bar(
            output.analytics_break_df, x="break_type", y="total_difference", title="Financial Difference by Break Type"
        )
        st.plotly_chart(chart2, use_container_width=True)
    if not output.analytics_period_df.empty:
        chart3 = px.line(
            output.analytics_period_df.sort_values("reporting_period"),
            x="reporting_period",
            y="total_difference",
            markers=True,
            title="Total Difference by Reporting Period",
        )
        st.plotly_chart(chart3, use_container_width=True)
        chart4 = px.line(
            output.analytics_period_df.sort_values("reporting_period"),
            x="reporting_period",
            y="open_breaks",
            markers=True,
            title="Open Breaks by Reporting Period",
        )
        st.plotly_chart(chart4, use_container_width=True)

    entity_impact = (
        output.reconciliation_df.assign(abs_difference=lambda frame: frame["difference"].abs())
        .groupby("legal_entity", as_index=False)
        .agg(total_difference=("abs_difference", "sum"))
        .sort_values("total_difference", ascending=False)
        .head(10)
    )
    if not entity_impact.empty:
        chart5 = px.bar(
            entity_impact,
            x="legal_entity",
            y="total_difference",
            color="total_difference",
            title="Top 10 Legal Entities by Difference",
        )
        st.plotly_chart(chart5, use_container_width=True)

    account_impact = (
        output.reconciliation_df.assign(abs_difference=lambda frame: frame["difference"].abs())
        .groupby("account_name", as_index=False)
        .agg(total_difference=("abs_difference", "sum"))
        .sort_values("total_difference", ascending=False)
        .head(10)
    )
    if not account_impact.empty:
        chart6 = px.bar(
            account_impact,
            x="account_name",
            y="total_difference",
            color="total_difference",
            title="Top 10 Accounts by Difference",
        )
        st.plotly_chart(chart6, use_container_width=True)

st.subheader("Downloads")
st.download_button(
    "Download Reconciliation Results",
    data=to_csv_bytes(output.reconciliation_df),
    file_name="reconciliation_results.csv",
    mime="text/csv",
)
st.download_button(
    "Download Break Analysis",
    data=to_csv_bytes(output.break_analysis_df),
    file_name="break_analysis.csv",
    mime="text/csv",
)
st.download_button(
    "Download PO Action Plan",
    data=to_csv_bytes(output.po_action_plan_df),
    file_name="po_action_plan.csv",
    mime="text/csv",
)
st.download_button(
    "Download Prioritized Backlog",
    data=to_csv_bytes(output.prioritized_backlog_df),
    file_name="prioritized_backlog.csv",
    mime="text/csv",
)
st.download_button(
    "Download Executive Summary",
    data=to_csv_bytes(output.executive_summary_df),
    file_name="executive_summary.csv",
    mime="text/csv",
)
