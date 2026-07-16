# AccessCatalog Agent

**A DataHub-powered accessibility compliance agent for public-sector document catalogs.**

> DataHub Agent Hackathon submission — *Agents That Do Real Work* track.

## The problem

Public agencies are legally required to make their documents accessible — Section 508 for US federal agencies, and under the DOJ's [ADA Title II web rule](https://www.ada.gov/resources/2024-03-08-web-rule/) state & local governments must meet WCAG 2.1 AA, with compliance deadlines from **April 2027**. The DOJ [extended those deadlines by a year in April 2026](https://www.federalregister.gov/documents/2026/04/20/2026-07663/extension-of-compliance-dates-for-nondiscrimination-on-the-basis-of-disability-accessibility-of-web) for one stated reason: entities aren't ready and technical solutions have lagged. Meanwhile a mid-size city publishes thousands of PDFs across dozens of departments, and nobody can answer:

- *Which of our public-facing documents are still inaccessible?*
- *Which department owns them?*
- *What should we remediate first?*
- *Has this document already been remediated somewhere?*

Spreadsheet trackers rot. Accessibility scans get run once and forgotten. The knowledge lives in nobody's head.

## The idea: the catalog is the compliance system of record

AccessCatalog Agent treats **documents as first-class catalog entities in [DataHub](https://datahub.com)**:

| Concept | DataHub entity |
|---|---|
| PDF document | Dataset on a custom `documents` platform |
| Department | Domain + Ownership (real owners, per document) |
| Compliance status | Tags: `unscanned` → `508-compliant` / `508-non-compliant` / `in-remediation` |
| Scan evidence | Custom properties (score, failed checks, timestamp, scanner version) |
| Original → remediated edition | **Lineage** |

An **agent** (OpenAI Agents SDK) closes the loop:

```
                    ┌──────────────── DataHub ────────────────┐
                    │  tags · ownership · lineage · properties │
                    └──────┬───────────────────────▲──────────┘
              reads via    │                       │  writes back via
         DataHub MCP Server│                       │  DataHub Python SDK
                    ┌──────▼───────────────────────┴──────────┐
                    │            AccessCatalog Agent           │
                    │  1. inventory unscanned docs (MCP search)│
                    │  2. REAL PDF accessibility scans         │
                    │  3. lineage-aware prioritization         │
                    │  4. remediation queue + status write-back│
                    │  5. compliance report                    │
                    └──────────────────────────────────────────┘
```

The agent **reads** the catalog through the [DataHub MCP Server](https://docs.datahub.com/docs/features/feature-guides/mcp) (`search`, `get_entities`, `get_lineage`) and **writes back** verdicts, evidence, and queue state — so the next person or agent inherits verified knowledge instead of starting over.

### What makes it interesting

- **Real scans, not mocks.** The scanner inspects actual PDF internals with `pikepdf`/`pypdf`: tag structure (`StructTreeRoot`/`MarkInfo`), document title, `/Lang`, image-only pages (untreated scans), form field labels, bookmarks — each mapped to Section 508 / WCAG criteria.
- **Lineage-aware judgment.** Before queueing a document, the agent checks DataHub lineage. If an accessible edition already exists downstream, it recommends redirecting the public URL instead of paying for duplicate remediation. That's a decision only possible *because* the catalog knows document lineage.
- **Guardrailed write-back.** The agent's `queue_remediation` tool *enforces* catalog consistency: it rejects attempts to queue compliant documents, internal documents, or documents that lineage shows are already remediated. Prompt instructions guide; tools guarantee.
- **Reports are views, not silos.** Compliance reports are generated from live catalog state — tags, properties, ownership, lineage — never from local files.

## Quick start

Prereqs: Docker (e.g. [OrbStack](https://orbstack.dev)), [uv](https://docs.astral.sh/uv/), and an OpenAI API key. The 22-PDF sample corpus is **pre-generated and committed** — nothing else to install.

```bash
git clone <this repo> && cd accesscatalog-agent

# 1. Python env + deps
uv venv --python 3.11 && source .venv/bin/activate
uv pip install -e . mcp-server-datahub

# 2. Local DataHub (takes a few minutes on first run)
datahub docker quickstart
# UI: http://localhost:9002  (user/pass: datahub/datahub)

# 3. Configure the agent
cp .env.example .env   # add your OPENAI_API_KEY

# 4. Run everything: ingest -> agent -> reports
./scripts/demo.sh
```

Or run the steps individually: `accesscatalog ingest`, `accesscatalog agent`, `accesscatalog report`, `accesscatalog status`.

You can watch the agent work in the DataHub UI: search `tags:unscanned`, refresh, and see documents flip to `508-non-compliant` / `508-compliant` / `in-remediation` in real time, with scan evidence in each dataset's properties.

> Want to regenerate the corpus from scratch? `brew install weasyprint`, then
> `uv pip install -e '.[corpus]' && python scripts/generate_corpus.py`
> (WeasyPrint is only needed for corpus generation — it produces genuinely
> tagged PDF/UA files, so the "compliant" samples are real, not mocked).

## CLI

| Command | What it does |
|---|---|
| `accesscatalog ingest` | Register the corpus in DataHub as unscanned inventory |
| `accesscatalog agent` | Full compliance pass: scan → write back → prioritize → queue |
| `accesscatalog report` | Markdown + HTML compliance reports from live catalog state |
| `accesscatalog status` | Per-department compliance table in the terminal |
| `accesscatalog scan <pdf>` | Scan any single PDF locally (no DataHub write) |

## Sample outputs

See [`examples/`](examples/) — a remediation queue, agent executive summary, and compliance reports produced by a real run against the sample corpus.

## Repository layout

```
accesscatalog/
  scanner/   # real PDF accessibility checks (Section 508 / WCAG mapped)
  ingest/    # DataHub ingestion + write-back (tags, evidence, lineage)
  agent/     # OpenAI Agents SDK runner + DataHub MCP + guardrailed tools
  report/    # compliance reports rendered from live catalog state
corpus/      # synthetic City of Rivergate PDF corpus + manifest
examples/    # sample outputs from a real agent run
scripts/     # corpus generator
```

## Troubleshooting

- **`Connection refused` on localhost:8080** — Docker (OrbStack) isn't running
  or the DataHub containers stopped. Start Docker, then re-run
  `datahub docker quickstart` (idempotent; it restarts existing containers)
  and wait until `curl -sf http://localhost:8080/health` succeeds.
- **Agent reports write-back failures** — same cause; the agent's tools
  surface DataHub write errors honestly instead of pretending they landed.
  Restore DataHub and re-run `accesscatalog agent`.
- **Re-running from scratch** — `accesscatalog ingest` resets every document
  to the `unscanned` baseline (tags, properties, lineage are re-emitted).

## Tech

DataHub (quickstart, Python SDK, MCP Server) · OpenAI Agents SDK · pikepdf / pypdf · WeasyPrint (PDF/UA corpus generation) · Typer + Rich

## License

Apache 2.0 — see [LICENSE](LICENSE).
