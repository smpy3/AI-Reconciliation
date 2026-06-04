# Project Brief (Hiring Manager Version)

## What this does
This solution turns one FRP reconciliation input file into:
- detected data breaks,
- control impact insights,
- delivery-ready Product Owner actions,
- prioritized backlog and PI plan,
- and a business case with ROI.

## Why this is different
Most demos only show charts.  
This demo shows how a Product Owner drives:
- risk reduction,
- release priorities,
- and leadership decisions using data.

## Input
Single CSV upload with:
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

## Outputs
1. **Reconciliation Results**  
   Matched, Missing in FRP, Orphan FRP Record, Amount Break, Duplicate Source.

2. **Break Analysis**  
   Root cause, owner, remediation recommendation, control impact.

3. **PO Action Plan**  
   User story, acceptance criteria, priority, blocker, decision needed.

4. **Prioritized Backlog**  
   Priority score, rank, owner, PI target (`Current PI` or `Next PI`).

5. **Business Case**  
   Value at Risk, estimated remediation cost, estimated savings, estimated ROI.

6. **Executive Summary**  
   Decision-focused summary for Product Group Owner and stakeholders.

## AI + non-AI mode
- No API key: deterministic and fully usable output.
- With API key: richer insights, escalation notes, and executive commentary.

## One-line pitch
“I built a Product Owner operating model that converts FRP data quality risks into measurable delivery decisions and ROI-backed action plans.”
