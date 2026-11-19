# Data dictionary

| Table | Grain | Primary key | Clean rows |
|---|---|---|---|
| tickets | Latest valid snapshot per ticket | ticket_id | 6,000 |
| teams | One fictional team | team_id | 3 |
| sla_policy | One SLA policy per priority | priority | 3 |

All timestamps are UTC. The fixed observation snapshot is **2026-01-01 00:00 UTC**. Durations and deadlines use calendar hours, including weekends. Timestamps are preserved as text in the Power BI import; derived duration/eligibility columns supply the measures.

| Fields | Definition |
|---|---|
| ticket_id | Unique ticket after retaining the latest snapshot |
| opened_at, first_response_at, resolved_at | Opening and observed outcome timestamps; absent outcomes stay null |
| updated_at | Snapshot version used to retain the latest row |
| team_id, priority, channel | Team FK, policy FK, and fictional intake channel |
| response_sla_hours, resolution_sla_hours | Priority-specific calendar-hour deadlines |
| age_hours, age_band | Age from opening to fixed observation snapshot; bands sort using numeric prefixes |
| response_hours, resolution_hours | Observed outcome duration; null if outcome not observed |
| response_eligible, resolution_eligible | 1 when outcome is observed OR deadline has elapsed |
| response_breach, resolution_breach | 1 when observed duration exceeds deadline OR outcome is absent at/after deadline |
| open_flag, overdue_open | Unresolved at snapshot; unresolved at/after resolution deadline |
| csat | Optional 1–5 survey response; missing is not a zero score |
| csat_responded, csat_positive | Response is present; observed response is at least 4 |
| month | Opening month, YYYY-MM |
| team, specialty | Fictional team label and remit |

Attainment = (SUM(eligible) − SUM(breach)) / SUM(eligible). Pending tickets still within deadline are excluded. Observed outcomes exactly at deadline pass; pending tickets at deadline count as overdue. Empty denominators return blank in DAX. CSAT positivity uses respondents only. Percentiles in `analysis/06_response_percentiles.csv` describe observed responses and do not substitute for SLA attainment.

[Machine-readable column profile](../analysis/data_dictionary.csv) lists inferred types, null counts and distinct counts. Both relationships are many-to-one and filter from dimension to fact.
