# Decision memo: support SLA performance

**Scope:** 6,000 synthetic tickets opened in 2025, observed at 2026-01-01 00:00 UTC. All deadlines use calendar hours, not business-hour calendars.

## Findings

Response SLA attainment is **79.6%** over 5,995 eligible tickets. Resolution attainment is 74.7%. There are 227 unresolved tickets, including 199 beyond their priority-specific resolution deadline. The weakest response cell is **Technical / High**, at 31.0% across 374 eligible tickets.

## Proposed decision

Review Technical-team routing, staffing and escalation coverage, especially late-year high-priority demand. Compare within priority before ranking teams; raw team averages mix different deadlines and workloads. Establish a daily overdue-backlog review and test a routing intervention with matched priority and channel strata.

## Denominators and censoring

A ticket is eligible once an outcome is observed or its deadline has elapsed. An unresolved/unanswered ticket past its deadline counts as a breach. Pending tickets still within the deadline are excluded, never counted as successes. An observed response exactly at the deadline meets SLA; pending at the deadline is operationally overdue at snapshot. Month is opening month, not response month. Recent cohorts may remain unstable. P50/P90/P95 response times describe observed responses only; they do not replace the censored SLA measure.

CSAT positivity is 70.3% among 1,934 respondents. Survey response rates differ by resolution speed; the score cannot be generalized to all customers. No missing CSAT value is filled with zero.

## Data quality

6,100 raw snapshot rows → keep the latest snapshot for each ticket (90 superseded rows removed) → quarantine 10 responses occurring before opening → 6,000 unique tickets. All IDs and timestamps are fictional. Timestamp monotonicity, denominator membership, overdue inclusion and dimension integrity are checked before publication.

## Limitations

The generator intentionally includes a late-year Technical-team slowdown. Findings are simulated and do not prove staffing caused a real decline. Reopens, reassignment, holidays, customer-wait pauses and event-level history are absent. Production SLA calculations would require contractual calendar and pause rules. Proposed improvements are hypotheses, not achieved impact.
