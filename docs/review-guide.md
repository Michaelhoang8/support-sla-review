# Review guide

1. Read the [decision memo](../analysis/findings.md) before viewing the report.
2. Open [SQL 01](../sql/01_sla_scorecard.sql) and compare its result with the overview cards. Cards abbreviate large currency values; the CSV preserves precision.
3. Review the [quarantine](../analysis/quarantine.csv) and [quality report](../analysis/quality_report.json). Identify which records were excluded and why.
4. Follow a measure from [DAX](../powerbi/measures.dax) through the [data dictionary](data-dictionary.md) to the cleaned CSV and SQL result.
5. Reproduce the filter in screenshot 02 and confirm totals by filtering the fact table. Page slicers are independent; switching pages does not carry the selection across.
6. Inspect the relationship capture. Dimension keys must be unique and all fact keys must have matches.
7. Re-run the automated checks. They independently compare published SQL outputs with the warehouse and test business rules.

## Questions to be ready to explain

- Why is a ratio of sums preferable to an average of percentages here?
- What is the fact-table grain, and how could a join accidentally multiply rows?
- Which null values carry business meaning?
- What observation window is needed for a fair comparison?
- Which recommendation needs a controlled experiment rather than a descriptive dashboard?
- What production source data and policy details are missing from this simulation?

The project demonstrates a reproducible analytical workflow. It does not establish real-world causal effects or savings.
