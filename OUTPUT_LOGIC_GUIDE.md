# Output Logic Guide (Simple + Detailed)

This document explains:
- what each output means,
- every column in each output,
- and the exact logic used.

---

## 1) Reconciliation Results

### What it does
Compares source amount (`oracle_amount`) and target amount (`frp_amount`) row by row.
Then tags each record with break type, severity, and status.

### Columns and logic
- `recon_id`  
  Auto ID created by app (example: `REC-001`).

- `record_id`  
  Original ID from uploaded file.

- `reporting_period`  
  Period from input (example: `2026-03`).

- `legal_entity`  
  Entity name from input.

- `account_code`  
  Account code from input.

- `account_name`  
  Account label from input.

- `cost_center`  
  Cost center from input.

- `product`  
  Product/group name from input.

- `currency`  
  Currency from input.

- `oracle_amount`  
  Source amount (converted to numeric).

- `frp_amount`  
  Target amount (converted to numeric).

- `difference`  
  Formula: `oracle_amount - frp_amount`.

- `break_type`  
  Rules:
  - `Missing in FRP` if `oracle_amount > 0` and `frp_amount = 0`
  - `Orphan FRP Record` if `oracle_amount = 0` and `frp_amount > 0`
  - `Amount Break` if both > 0 and amounts are different
  - `Potential Duplicate Source` if duplicate key exists
  - else `Matched`

- `severity`  
  Rules:
  - `High` if missing/orphan
  - `Medium` if duplicate
  - for amount breaks:
    - `High` if abs(diff) >= 10,000
    - `Medium` if abs(diff) >= 5,000
    - `Low` otherwise
  - `None` for matched

- `status`  
  `Passed` if matched, else `Open`.

---

## 2) Break Analysis

### What it does
Only keeps non-matched records and adds owner + action + impact text.

### Columns and logic
- `recon_id`  
  Links back to reconciliation row.

- `break_type`  
  Copied from reconciliation output.

- `likely_root_cause`  
  Template based on break type.

- `recommended_owner`  
  Mapping:
  - Missing in FRP → `Technology/Data Team`
  - Orphan FRP Record → `Finance Control Owner`
  - Amount Break → `Finance Data Owner`
  - Potential Duplicate Source → `Data Quality Team`

- `recommended_action`  
  Template action based on break type.

- `business_impact`  
  Template based on severity (High/Medium/Low).

- `control_impact`  
  Control statement based on break type.

---

## 3) PO Action Plan

### What it does
Converts break analysis into delivery-ready backlog actions.

### Columns and logic
- `action_id`  
  Auto ID (example: `ACT-001`).

- `recon_id`  
  Link to source break.

- `product_owner_action`  
  Action title generated from break type.

- `user_story`  
  Template story using account name + break type.

- `acceptance_criteria`  
  Fixed checklist template:
  detection, owner assignment, evidence, retest.

- `priority`  
  `High` if severity high, else `Medium`.

- `dependency`  
  Fixed dependency text.

- `blocker`  
  Fixed blocker text.

- `decision_needed`  
  Fixed decision text.

---

## 4) Prioritized Backlog

### What it does
Ranks PO actions by business urgency using scoring.

### Columns and logic
- `backlog_id`  
  `ACT-xxx` converted to `FRP-xxx`.

- `recon_id`  
  Source row link.

- `feature`  
  PO action title.

- `break_type`  
  Source break type.

- `severity`  
  Source severity.

- `difference`  
  Source difference amount.

- `priority_score`  
  Formula:
  - Severity points (High=10, Medium=6, Low=3, None=1) * 0.35
  - Break type bonus * 0.30
  - Magnitude factor (`min(abs(diff)/20000, 10)`) * 0.25
  - Effort penalty * 0.10

- `recommended_rank`  
  Sorted by `priority_score` descending (1 is top priority).

- `pi_target`  
  `Current PI` if score >= 6, else `Next PI`.

- `owner`  
  Owner mapped from break type.

---

## 5) Executive Summary

### What it does
Creates a manager-friendly summary table.

### Columns and logic
- `section`  
  Label name (Overall Status, Summary, Key Risks, etc.).

- `generated_summary`  
  Generated text for that section.

### Status logic
- `Green`: no open breaks
- `Amber`: open breaks exist, but high severity count < 3
- `Red`: high severity count >= 3

---

## Related metrics shown on top
- Total Records
- Matched Records
- Open Breaks
- High Severity Breaks
- Medium Severity Breaks
- Total Dollar Difference
- PO Actions Created

## Business Case metrics
- Value at Risk
- Estimated Remediation Cost
- Estimated Savings
- Estimated ROI
- Actions in Scope
