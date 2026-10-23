# Data QA Worker Agent

A first deterministic worker for an agent-to-agent services marketplace. It inspects local CSV/JSON files and returns a machine-readable quality report that another agent can consume.

## Supported checks

- CSV: empty files, blank/duplicate headers, blank rows, malformed row widths, exact duplicate rows.
- JSON: parse validity and root shape.
- Output: JSON report with findings, severity, counts, status, and explicit limitations.

## Run locally

From the repository root:

```bash
python -m data_qa_agent.cli sample.csv --out output/report.json
python -m data_qa_agent.cli sample.json --out output/report.json
python -m unittest discover -s tests -v
```

No input file is uploaded. The worker does not call external APIs, accept marketplace tasks, sign transactions, or move funds.

## Marketplace status

This is a runnable service prototype, not yet a registered or hired marketplace agent. Before offering it for paid work, validate the marketplace's current task format, delivery/acceptance rules, permitted pricing, and fee attribution. Do not represent proposed commissions as income. Use non-sensitive sample files until a data-handling agreement is in place.

## Example deliverable

A JSON file with `status`, row/column counts where applicable, findings, severity and limitations. Findings are preliminary signals and require human/business-rule review.
