"""The AccessCatalog agent: OpenAI Agents SDK + DataHub MCP server.

Read the catalog through MCP -> scan real PDFs -> write verdicts back ->
build a lineage-aware remediation queue -> leave the catalog better than
it was found.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from agents import Agent, ModelSettings, Runner, set_tracing_disabled
from agents.mcp import MCPServerStdio

from accesscatalog.agent.tools import (
    AgentContext,
    get_queue_status,
    queue_remediation,
    scan_document,
)
from accesscatalog.ingest import get_graph, load_manifest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

INSTRUCTIONS = """\
You are AccessCatalog Agent, an accessibility compliance agent for the City of
Rivergate's public document library. The catalog lives in DataHub; you read it
through the DataHub MCP tools and act with your local tools.

Your job, in order:

1. INVENTORY — Use the MCP `search` tool with query `tags:unscanned` to find
   every document that has not been checked (they are datasets on the
   `documents` platform; ignore the tag entity itself in results). Then use
   `get_entities` (batch the URNs) to pull each document's customProperties
   (documentId, publicFacing, monthlyViews, department, publishedDate).

2. SCAN — For EVERY unscanned document, call `scan_document` with its
   documentId. This runs a real PDF accessibility scan and writes the verdict
   back to DataHub automatically. Do not skip any document.

3. PRIORITIZE — Build a remediation queue from the non-compliant documents.
   Rules (the queue_remediation tool also ENFORCES these and will reject
   violating calls — a rejection means re-check your reasoning, not retry):
   - NEVER queue a document whose scan verdict was compliant. Compliant
     documents are done; they appear in the summary, not the queue.
   - Only queue PUBLIC-FACING documents (publicFacing=true). Internal
     documents are noted in your summary but not queued.
   - BEFORE queueing a document, check its lineage with the MCP `get_lineage`
     tool (direction: downstream). If a remediated/accessible edition already
     exists downstream, DO NOT queue it — record a "redirect" recommendation
     instead (the city should point the public URL at the accessible edition
     and archive the original).
   - Rank the remaining documents by real-world impact: monthly views first,
     then severity (scanned image-only documents are worse than merely
     untagged ones; documents that fail more critical checks rank higher at
     similar traffic), then age.

4. ACT — Call `queue_remediation` once per document, strictly in priority
   order (most urgent first — the tool assigns queue positions from call
   order). Give a concrete rationale that cites the evidence: traffic,
   failed checks, lineage findings, department.

5. VERIFY — Call `get_queue_status` and reconcile it against what you
   intended: every document you meant to queue must appear there with the
   position you expect. If one is missing, its write-back failed — queue it
   again or report the failure explicitly. Never describe a document as
   queued unless get_queue_status confirms it. Use its `verdict_counts` and
   `verdicts_by_visibility` as the authoritative numbers in your summary —
   do not recount by hand.

6. REPORT — Finish with an executive summary in Markdown:
   - Overall compliance posture (counts by verdict, public vs internal)
   - The remediation queue as a table (position, title, department, owner,
     views, failed checks, rationale)
   - Redirect recommendations from the lineage analysis
   - Per-department one-line status, naming the responsible owner

Be precise: never invent scan results, views, or owners — everything you
state must come from the catalog or from your tools. If a tool errors,
say so rather than guessing.
"""

TASK = (
    "Run the full compliance pass over the document catalog: inventory, scan "
    "everything unscanned, build the lineage-aware remediation queue, and "
    "produce the executive summary."
)


def _find_accessible_editions(graph, manifest: dict) -> set[str]:
    """doc_ids whose catalog lineage already has a downstream accessible
    edition — the queue_remediation guardrail uses this to reject duplicates.

    Read from the catalog (not the manifest) so the guardrail reflects what
    DataHub actually knows.
    """
    import datahub.metadata.schema_classes as models

    from accesscatalog.ingest import document_urn

    urn_to_id = {document_urn(d): d["id"] for d in manifest["documents"]}
    sources: set[str] = set()
    for doc in manifest["documents"]:
        upstream = graph.get_aspect(document_urn(doc), models.UpstreamLineageClass)
        if upstream:
            for up in upstream.upstreams:
                if up.dataset in urn_to_id:
                    sources.add(urn_to_id[up.dataset])
    return sources


async def run_agent(
    server_url: str = "http://localhost:8080",
    model: str | None = None,
    out_dir: Path | None = None,
) -> dict:
    set_tracing_disabled(True)
    model = model or os.getenv("ACCESSCATALOG_MODEL", "gpt-5.1")
    out_dir = out_dir or REPO_ROOT / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    graph = get_graph(server_url)
    manifest = load_manifest(REPO_ROOT / "corpus/manifest.yaml")
    context = AgentContext(
        graph=graph,
        manifest=manifest,
        repo_root=REPO_ROOT,
        accessible_editions=_find_accessible_editions(graph, manifest),
    )

    # mcp-server-datahub lives next to the current interpreter (same venv).
    mcp_datahub = MCPServerStdio(
        name="datahub",
        params={
            "command": str(Path(sys.executable).parent / "mcp-server-datahub"),
            "env": {**os.environ, "DATAHUB_GMS_URL": server_url},
        },
        cache_tools_list=True,
        client_session_timeout_seconds=60,
    )

    async with mcp_datahub:
        agent = Agent(
            name="AccessCatalog Agent",
            instructions=INSTRUCTIONS,
            model=model,
            mcp_servers=[mcp_datahub],
            tools=[scan_document, queue_remediation, get_queue_status],
            # Sequential tool calls: queue positions come from call order,
            # so parallel execution would scramble priorities.
            model_settings=ModelSettings(parallel_tool_calls=False),
        )
        result = await Runner.run(agent, TASK, context=context, max_turns=120)

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    queue_path = out_dir / "remediation_queue.json"
    queue_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "municipality": context.manifest["municipality"],
                "scanned": len(context.scans),
                "queue": sorted(context.queue, key=lambda e: e["position"]),
            },
            indent=2,
        )
    )
    summary_path = out_dir / "agent_summary.md"
    summary_path.write_text(str(result.final_output))

    return {
        "scanned": len(context.scans),
        "queued": len(context.queue),
        "queue_file": str(queue_path),
        "summary_file": str(summary_path),
        "run_stamp": run_stamp,
        "final_output": str(result.final_output),
    }
