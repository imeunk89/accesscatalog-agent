# Sample outputs

Artifacts produced by a **real agent run** against the sample corpus
(22 municipal PDFs, City of Rivergate) — included so judges can evaluate
output quality without running the stack.

| File | What it is |
|---|---|
| `remediation_queue.json` | The prioritized remediation queue the agent wrote back to DataHub — position, ownership, traffic, failed checks, and the agent's rationale for every entry |
| `agent_summary.md` | The agent's executive summary: compliance posture, queue, redirect recommendations from lineage analysis, per-department status |
| `compliance_report.md` | Department-level compliance report generated from **live DataHub catalog state** (tags, properties, ownership, lineage) |
| `compliance_report.html` | Same report, styled HTML |
| `scan_result_sample.json` | Raw scanner output for one document — every check with its Section 508 / WCAG mapping and evidence |

How these were made:

```bash
accesscatalog ingest    # catalog: 22 docs, all tagged `unscanned`
accesscatalog agent     # scan → write-back → lineage-aware queue
accesscatalog report    # views over live catalog state
```
