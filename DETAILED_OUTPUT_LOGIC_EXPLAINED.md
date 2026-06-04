# FRP Output Logic — Detailed Simple Guide

This guide explains in simple words:
- what each output does,
- how each column is created,
- what formula/rule is used,
- and why it is useful for business and Product Owner decisions.

---

## 0) Input (the one uploaded CSV)

Required columns:
- `record_id`
- `reporting_period`
- `legal_entity`
- `account_code`
- `account_name`
- `cost_center`
- `product`
- `currency`
- `oracle_amount`
- `frp_amount`
- `source_system`

### How app uses input
The app compares `oracle_amount` (source) vs `frp_amount` (target) row-by-row.
Then it classifies each row as matched or break.

---

## 1) Reconciliation Results

## Purpose
This is the **base output**.  
It tells which rows are clean and which rows have issues.

## Columns, logic, use

### `recon_id`
- How it comes: auto-generated sequence (`REC-001`, `REC-002`, ...).
- Use: unique internal id to link all other outputs.

### `record_id`
- How it comes: copied from input.
- Use: original row traceability.

### `reporting_period`
- How it comes: copied from input.
- Use: trend analysis by month/quarter.

### `legal_entity`
- How it comes: copied from input.
- Use: identify where risk is concentrated.

### `account_code`, `account_name`
- How it comes: copied from input.
- Use: identify which finance line has issue.

### `cost_center`
- How it comes: copied from input.
- Use: ownership and operational follow-up.

### `product`
- How it comes: copied from input.
- Use: business segment impact.

### `currency`
- How it comes: copied from input.
- Use: amount interpretation.

### `oracle_amount`
- How it comes: input value converted to numeric.
- Use: source “expected” amount.

### `frp_amount`
- How it comes: input value converted to numeric.
- Use: target “reported” amount.

### `difference`
- Formula: `oracle_amount - frp_amount`
- Use: size of mismatch.

### `break_type`
- Rules:
  - `Missing in FRP` → `oracle_amount > 0` and `frp_amount = 0`
  - `Orphan FRP Record` → `oracle_amount = 0` and `frp_amount > 0`
  - `Amount Break` → both > 0 and difference ≠ 0
  - `Potential Duplicate Source` → duplicate key rows based on  
    (`reporting_period`, `legal_entity`, `account_code`, `cost_center`, `oracle_amount`)
  - else `Matched`
- Use: standard category for triage.

### `severity`
- Rules:
  - `Missing in FRP` and `Orphan FRP Record` => `High`
  - `Potential Duplicate Source` => `Medium`
  - `Amount Break`:
    - `High` if `abs(difference) >= 10000`
    - `Medium` if `abs(difference) >= 5000`
    - `Low` otherwise
  - `Matched` => `None`
- Use: urgency for prioritization.

### `status`
- Rule:
  - `Passed` if `break_type = Matched`
  - `Open` otherwise
- Use: open issue tracking.

## Business help
- Gives immediate data quality health.
- Creates a factual base for decisions and delivery scope.

---

## 2) Break Analysis

## Purpose
Turns raw breaks into actionable diagnosis:
- likely cause,
- owner,
- action,
- control impact.

## Columns, logic, use

### `recon_id`
- From reconciliation output.
- Use: row linkage.

### `break_type`
- From reconciliation output.
- Use: issue category.

### `likely_root_cause`
- Rule-based text by break type:
  - Missing in FRP => load/ingestion scope miss
  - Orphan FRP Record => no valid source lineage
  - Amount Break => mapping/transformation mismatch
  - Potential Duplicate Source => duplicate transaction in source
- Use: faster root-cause discussion.

### `recommended_owner`
- Rule mapping:
  - Missing in FRP => `Technology/Data Team`
  - Orphan FRP Record => `Finance Control Owner`
  - Amount Break => `Finance Data Owner`
  - Potential Duplicate Source => `Data Quality Team`
- Use: clear accountability.

### `recommended_action`
- Rule-based next step by break type.
- Use: short-term remediation guidance.

### `business_impact`
- Rule from severity:
  - High => strong reporting/close risk
  - Medium => operational quality risk
  - Low => monitor
- Use: leadership impact communication.

### `control_impact`
- Rule by break type:
  - completeness, lineage, amount accuracy, or duplicate control
- Use: control framework reporting.

## Business help
- Reduces “who should do what” confusion.
- Speeds incident-to-action conversion.

---

## 3) PO Action Plan

## Purpose
Converts each break into a backlog-ready Product Owner item.

## Columns, logic, use

### `action_id`
- Auto sequence: `ACT-001`, `ACT-002`, ...
- Use: track PO tasks.

### `recon_id`
- Linked break id.
- Use: traceability to source issue.

### `product_owner_action`
- Template text: “Create remediation backlog item for …”
- Use: action title for board.

### `user_story`
- Template story using `account_name` + break type.
- Use: Agile-ready requirement format.

### `acceptance_criteria`
- Standard 4-step checklist:
  1) detect issue
  2) assign owner
  3) log evidence
  4) re-test pass
- Use: defines done state.

### `priority`
- Rule:
  - `High` if source severity is High
  - else `Medium`
- Use: sprint/PI planning.

### `dependency`
- Fixed text: source-target mapping/control evidence.
- Use: implementation readiness.

### `blocker`
- Fixed text: business signoff pending.
- Use: escalation visibility.

### `decision_needed`
- Fixed text: confirm threshold and release timing.
- Use: governance decisions.

## Business help
- Makes data issues deliverable in Agile flow.
- Bridges analytics to execution.

---

## 4) Prioritized Backlog

## Purpose
Ranks PO actions with a numeric score, then suggests PI target.

## Columns, logic, use

### `backlog_id`
- Derived from `action_id` by replacing `ACT` with `FRP`.
- Use: feature-style tracking id.

### `recon_id`
- Source link.
- Use: traceability.

### `feature`
- Copied from `product_owner_action`.
- Use: backlog title.

### `break_type`, `severity`, `difference`
- Copied from reconciliation source row.
- Use: risk and impact context.

### `priority_score`
- Formula:
  - `severity_points * 0.35`
  - `+ break_type_bonus * 0.30`
  - `+ min(abs(difference)/20000, 10) * 0.25`
  - `- effort * 0.10`

Where:
- Severity points: High=10, Medium=6, Low=3, None=1
- Break type bonus:
  - Missing in FRP=9
  - Orphan FRP Record=8
  - Amount Break=7
  - Potential Duplicate Source=5
  - Matched=0
- Effort:
  - 6 for Missing/Orphan
  - 4 for others

- Use: objective ordering of work.

### `recommended_rank`
- Rule: sorted by `priority_score` descending; 1 is highest.
- Use: top-first implementation order.

### `pi_target`
- Rule:
  - `Current PI` if score >= 6
  - `Next PI` otherwise
- Use: release planning.

### `owner`
- Same mapping as Break Analysis owner.
- Use: execution responsibility.

## Business help
- Replaces subjective prioritization with transparent scoring.
- Helps PO defend roadmap decisions.

---

## 5) Executive Summary

## Purpose
One-page management view of health, risks, decisions, and next steps.

## Columns, logic, use

### `section`
- Name of summary block:
  - Overall Status
  - Summary
  - Key Risks
  - Control Impact
  - Decisions Needed
  - Next Steps

### `generated_summary`
- Generated text for each section.

## Key logic

### Overall Status
- `Green` => open breaks = 0
- `Amber` => open breaks > 0 and high severity breaks < 3
- `Red` => high severity breaks >= 3

### Summary
- “Processed X records and identified Y open breaks.”

### Key Risks
- Top 3 break types by frequency.

### Next Steps
- Number of PO actions and high-severity closure direction.

## Business help
- Ready for weekly leadership update.
- Keeps decisions focused and fast.

---

## 6) Analytics Tab (charts)

## Purpose
Visual understanding of risk, trend, concentration, and delivery load.

## Charts and logic

### Severity Distribution
- Source: Reconciliation Results
- X: severity, Y: count
- Helps: see risk mix quickly.

### Passed vs Open Status (donut)
- Source: Reconciliation Results
- Helps: quality health snapshot.

### Financial Impact by Break Type
- Source: break summary
- Y uses sum of `abs(difference)`
- Helps: know which break type costs most.

### PO Action Priority Mix
- Source: PO Action Plan
- Counts High vs Medium actions
- Helps: workload urgency.

### Priority Score vs Financial Difference
- Source: Prioritized Backlog
- Helps: compare urgency score vs money impact.

### Current PI vs Next PI
- Source: Prioritized Backlog `pi_target`
- Helps: planning distribution.

### Total Financial Difference by Reporting Period
- Source: Reconciliation Results grouped by period
- Y uses sum of `abs(difference)`
- Helps: trend by month/quarter.

### Top Legal Entities by Financial Difference
- Source: Reconciliation Results grouped by entity
- Y uses sum of `abs(difference)`
- Helps: concentration risk identification.

---

## 7) Top metrics (header cards)

### Summary Metrics
- Total Records
- Matched Records
- Open Breaks
- High Severity Breaks
- Medium Severity Breaks
- Total Dollar Difference (`sum(abs(difference))`)
- PO Actions Created

### Business Case Metrics
- Value at Risk = sum of `abs(difference)` for `Open` records
- Estimated Remediation Cost = `max(open_breaks*3,8) * 140`
- Estimated Savings = `Value at Risk * expected_reduction`
  - expected_reduction = 0.55 if high breaks >=3 else 0.35
- Estimated ROI = `(Savings - Cost) / Cost * 100`
- Actions in Scope = count of PO actions

## Business help
- Converts technical output into value narrative (risk vs cost vs return).

---

## 8) AI mode vs non-AI mode

### Non-AI mode
- All outputs above are generated using deterministic rules.
- Stable and reproducible.

### AI mode (if `OPENAI_API_KEY` set)
- Adds extra insight rows (`ai_root_cause`, `ai_recommendation`, `escalation_note`) when available.
- Adds extra executive commentary when available.

## Business help
- Non-AI = baseline reliability.
- AI = richer communication and faster decision support.

