# Devpost 제출 텍스트 초안

## Project name

AccessCatalog Agent

## Tagline (한 줄)

A DataHub-powered agent that turns your document catalog into an accessibility
compliance system of record — real PDF scans, lineage-aware prioritization,
and write-back so knowledge compounds.

## Text description (제출 폼용)

### Inspiration

The DOJ's ADA Title II rule requires US state & local governments to make
their web content and documents WCAG 2.1 AA accessible, with deadlines from
April 2027. In April 2026 the DOJ extended those deadlines by a full year —
citing resource constraints and technical solutions (including generative AI)
that have lagged expectations. In other words: the regulator itself confirmed
that governments cannot get this done with today's tooling. Federal agencies
have lived under Section 508 for years, and disability advocates are already
suing over the delay. Yet agencies publish thousands of PDFs across dozens of
departments with no way to answer: which public documents are inaccessible,
who owns them, and what should we fix first? Accessibility scans get run once
and forgotten in spreadsheets. We built AccessCatalog Agent to make the
catalog — not a spreadsheet — the compliance system of record.

Sources: [DOJ web rule fact sheet](https://www.ada.gov/resources/2024-03-08-web-rule/) ·
[Federal Register — compliance date extension (Apr 2026)](https://www.federalregister.gov/documents/2026/04/20/2026-07663/extension-of-compliance-dates-for-nondiscrimination-on-the-basis-of-disability-accessibility-of-web) ·
[DOJ ADA enforcement cases](https://www.ada.gov/cases/) ·
[Advocates sue over the delay (GovExec, May 2026)](https://www.govexec.com/management/2026/05/disability-advocates-sue-over-website-accessibility-delays/413785/)

### What it does

AccessCatalog Agent models a government document library as first-class
DataHub entities: PDFs are datasets on a custom `documents` platform,
departments are Domains with real Owners, compliance status is Tags, scan
evidence is custom properties, and remediation history is **Lineage**
(original → accessible edition).

An agent built on the OpenAI Agents SDK then closes the loop:

1. **Reads** the catalog through the DataHub MCP Server (search, get_entities,
   get_lineage) to inventory unscanned documents.
2. **Scans** each PDF for real accessibility failures — tag structure
   (StructTreeRoot/MarkInfo), document title, /Lang, image-only scanned pages,
   form labels — each check mapped to Section 508 / WCAG criteria.
3. **Writes back** verdicts as status tags and evidence properties, so the
   next person or agent inherits verified knowledge.
4. **Prioritizes** remediation: public-facing first, ranked by traffic and
   severity — and because it reads lineage, it detects documents that already
   have an accessible edition downstream and recommends a URL redirect instead
   of paying for duplicate remediation.
5. **Reports**: department-level compliance reports (Markdown/HTML) generated
   entirely from live catalog state, with named owners.

A key design decision: the agent's write-back tools *enforce* catalog
consistency. `queue_remediation` rejects compliant documents, internal
documents, and documents lineage shows are already remediated. Prompts guide;
tools guarantee.

### How we built it

- **DataHub** (docker quickstart) as the metadata backbone; Python SDK for
  ingestion & write-back; **DataHub MCP Server** for agent reads.
- **OpenAI Agents SDK** for the agent loop (MCP stdio integration + function
  tools).
- **pikepdf / pypdf** for real PDF internals inspection.
- **WeasyPrint (PDF/UA)** + reportlab + Pillow to generate a 22-document
  synthetic municipal corpus with genuinely accessible and inaccessible PDFs —
  including untagged text PDFs, image-only "scans", metadata-stripped exports,
  and remediation pairs connected by lineage.
- **Typer/Rich CLI**: `ingest`, `agent`, `report`, `status`, `scan`.

### Challenges / what we learned

- Producing *genuinely* tagged PDF/UA files (not mocked metadata) so the
  scanner demo is real end-to-end.
- Agent judgment fails in predictable ways (queueing a compliant doc because
  it had high traffic) — moving constraints from the prompt into tool-level
  guardrails fixed it permanently and made the system honest.
- OSS DataHub MCP Server is read-only (mutation tools disabled), which led to
  a clean architecture: MCP for reads, SDK-backed tools for writes.

### What's next

Content-aware checks (alt-text quality via vision models), DataHub Actions to
auto-scan on ingestion, connectors for real CMS/document stores, and multi-
agent remediation (an agent that actually fixes the PDFs and publishes the
accessible edition with lineage).

## 제출 체크리스트

- [ ] GitHub repo 공개 + Apache 2.0 (About 섹션에 라이선스 표시 확인)
- [ ] README에 셋업 가이드 (완료)
- [ ] examples/ 샘플 산출물 (완료 예정)
- [ ] 데모 영상 3분 이하, YouTube/Vimeo 공개 업로드
- [ ] 프로젝트 URL (= repo URL)
