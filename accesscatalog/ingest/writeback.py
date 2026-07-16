"""Write agent results back into DataHub.

This is the half of the loop that makes the catalog useful to the NEXT person
or agent: scan verdicts become tags, scan evidence becomes custom properties,
and remediation queue decisions become visible catalog state.
"""

from __future__ import annotations

from datetime import datetime, timezone

import datahub.metadata.schema_classes as models
from datahub.emitter.mce_builder import make_tag_urn
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.graph.client import DataHubGraph

from accesscatalog.scanner import ScanResult

STATUS_TAGS = {"unscanned", "508-compliant", "508-non-compliant", "in-remediation"}


def apply_scan_result(graph: DataHubGraph, urn: str, result: ScanResult) -> str:
    """Record a scan verdict on a document: status tag + evidence properties."""
    verdict = "508-compliant" if result.compliant else "508-non-compliant"
    _set_status_tag(graph, urn, verdict)

    props = graph.get_aspect(urn, models.DatasetPropertiesClass)
    if props is None:
        raise ValueError(f"Dataset not found in catalog: {urn}")
    failed = [c.check_id for c in result.failed_checks()]
    props.customProperties.update(
        {
            "accessibilityScore": str(result.score),
            "accessibilityCompliant": str(result.compliant).lower(),
            "criticalFailures": str(result.critical_failures),
            "failedChecks": ", ".join(failed) if failed else "none",
            "lastScannedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "scanner": "accesscatalog-agent/0.1",
        }
    )
    graph.emit_mcp(MetadataChangeProposalWrapper(entityUrn=urn, aspect=props))
    return verdict


def mark_in_remediation(graph: DataHubGraph, urn: str, queue_position: int) -> None:
    """Flag a document as queued for remediation, with its queue position."""
    _set_status_tag(graph, urn, "in-remediation")
    props = graph.get_aspect(urn, models.DatasetPropertiesClass)
    if props is None:
        raise ValueError(f"Dataset not found in catalog: {urn}")
    props.customProperties.update(
        {
            "remediationQueuePosition": str(queue_position),
            "remediationQueuedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )
    graph.emit_mcp(MetadataChangeProposalWrapper(entityUrn=urn, aspect=props))


def _set_status_tag(graph: DataHubGraph, urn: str, status: str) -> None:
    """Replace any existing status tag while preserving non-status tags."""
    existing = graph.get_aspect(urn, models.GlobalTagsClass) or models.GlobalTagsClass(tags=[])
    kept = [
        assoc
        for assoc in existing.tags
        if assoc.tag.split(":")[-1] not in STATUS_TAGS
    ]
    kept.append(models.TagAssociationClass(tag=make_tag_urn(status)))
    graph.emit_mcp(
        MetadataChangeProposalWrapper(
            entityUrn=urn, aspect=models.GlobalTagsClass(tags=kept)
        )
    )
