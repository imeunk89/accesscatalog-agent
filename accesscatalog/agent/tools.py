"""Local action tools for the AccessCatalog agent.

The agent READS the catalog through the DataHub MCP server. These tools are
its hands: they run real PDF accessibility scans and write the results back
into DataHub so the catalog always reflects verified state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from agents import RunContextWrapper, function_tool
from datahub.ingestion.graph.client import DataHubGraph

from accesscatalog.ingest import (
    apply_scan_result,
    document_urn,
    mark_in_remediation,
)
from accesscatalog.scanner import scan


@dataclass
class AgentContext:
    graph: DataHubGraph
    manifest: dict
    repo_root: Path
    #: doc_ids that already have an accessible downstream edition in catalog
    #: lineage — queueing them would duplicate finished remediation work.
    accessible_editions: set[str] = field(default_factory=set)
    scans: dict[str, dict] = field(default_factory=dict)
    queue: list[dict] = field(default_factory=list)

    @property
    def docs_by_id(self) -> dict[str, dict]:
        return {d["id"]: d for d in self.manifest["documents"]}


@function_tool
def scan_document(ctx: RunContextWrapper[AgentContext], document_id: str) -> dict:
    """Run a real PDF accessibility scan on a document and write the verdict
    back to DataHub (status tag + evidence properties).

    Args:
        document_id: The documentId custom property, e.g. "pw-snow-plan".
            (This is the last path segment of the dataset URN.)

    Returns the verdict, score (0-100), and the list of failed checks.
    """
    state = ctx.context
    doc = state.docs_by_id.get(document_id)
    if doc is None:
        return {"error": f"Unknown document_id: {document_id!r}"}

    result = scan(state.repo_root / doc["file"])
    try:
        verdict = apply_scan_result(state.graph, document_urn(doc), result)
    except Exception as exc:  # DataHub write failed — tell the model the truth
        return {
            "error": f"Scan ran but DataHub write-back FAILED for "
            f"{document_id}: {exc}. The catalog was NOT updated. Report "
            "this failure honestly in your summary.",
        }
    summary = {
        "document_id": document_id,
        "verdict": verdict,
        "score": result.score,
        "compliant": result.compliant,
        "failed_checks": [
            {"check": c.check_id, "standard": c.standard, "detail": c.detail}
            for c in result.failed_checks()
        ],
    }
    state.scans[document_id] = summary
    return summary


@function_tool
def queue_remediation(
    ctx: RunContextWrapper[AgentContext],
    document_id: str,
    rationale: str,
) -> dict:
    """Add a document to the remediation queue: tags it `in-remediation` in
    DataHub and records its queue position and the reasoning.

    Call this in PRIORITY ORDER — most urgent document first. Queue positions
    are assigned automatically from call order (first call = position 1).

    Args:
        document_id: The documentId custom property, e.g. "pw-snow-plan".
        rationale: One or two sentences explaining WHY this priority —
            cite public visibility, traffic, failure severity, and lineage.
    """
    state = ctx.context
    doc = state.docs_by_id.get(document_id)
    if doc is None:
        return {"error": f"Unknown document_id: {document_id!r}"}

    # Guardrails: the queue must never contradict catalog state. These are
    # enforced here — not just in the prompt — so a misjudged call fails
    # loudly instead of polluting the catalog.
    scan_summary = state.scans.get(document_id)
    if scan_summary is None:
        return {
            "rejected": document_id,
            "reason": "Document has not been scanned in this run. Scan it first.",
        }
    if scan_summary["compliant"]:
        return {
            "rejected": document_id,
            "reason": "Scan verdict is COMPLIANT — compliant documents are "
            "never queued for remediation.",
        }
    if not doc["public_facing"]:
        return {
            "rejected": document_id,
            "reason": "Internal document — only public-facing documents are "
            "queued. Note it in the summary instead.",
        }
    if document_id in state.accessible_editions:
        return {
            "rejected": document_id,
            "reason": "Catalog lineage shows an accessible edition already "
            "exists downstream. Recommend a URL redirect instead of queueing.",
        }

    position = len(state.queue) + 1
    try:
        mark_in_remediation(state.graph, document_urn(doc), position)
    except Exception as exc:  # DataHub write failed — tell the model the truth
        return {
            "error": f"DataHub write-back FAILED for {document_id}: {exc}. "
            "The document was NOT queued. Report this failure honestly in "
            "your summary.",
        }
    entry = {
        "position": position,
        "document_id": document_id,
        "title": doc["title"],
        "department": doc["department"],
        "owner": state.manifest["departments"][doc["department"]]["owner"],
        "public_facing": doc["public_facing"],
        "monthly_views": doc["monthly_views"],
        "failed_checks": [
            c["check"] for c in state.scans.get(document_id, {}).get("failed_checks", [])
        ],
        "rationale": rationale,
    }
    state.queue.append(entry)
    return {"queued": document_id, "position": position}


@function_tool
def get_queue_status(ctx: RunContextWrapper[AgentContext]) -> dict:
    """Return the AUTHORITATIVE state of this run: which documents were
    actually scanned (with verdicts) and which are actually in the
    remediation queue (with positions).

    Call this before writing your final summary and reconcile against it —
    if a document you intended to queue is missing here, its write-back
    failed and you must either queue it again or report the failure.
    """
    state = ctx.context
    verdicts = {"508-compliant": 0, "508-non-compliant": 0}
    by_visibility = {
        "public_facing": {"508-compliant": 0, "508-non-compliant": 0},
        "internal": {"508-compliant": 0, "508-non-compliant": 0},
    }
    for doc_id, s in state.scans.items():
        verdicts[s["verdict"]] += 1
        doc = state.docs_by_id.get(doc_id, {})
        bucket = "public_facing" if doc.get("public_facing") else "internal"
        by_visibility[bucket][s["verdict"]] += 1
    return {
        "scanned": len(state.scans),
        "verdict_counts": verdicts,
        "verdicts_by_visibility": by_visibility,
        "queued": [
            {"position": e["position"], "document_id": e["document_id"]}
            for e in sorted(state.queue, key=lambda e: e["position"])
        ],
    }
