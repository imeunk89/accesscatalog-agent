"""Ingest the document catalog into DataHub.

Models the document library as first-class DataHub entities:

  PDF document            -> Dataset on the custom `documents` platform
  Department              -> Domain (+ CorpUser ownership)
  Compliance status       -> Tags (applied later by the agent's write-back)
  Original -> remediated  -> Dataset lineage
  Public URL              -> externalUrl + institutional memory link

Ingestion deliberately registers documents as UNSCANNED inventory. Scanning,
verdicts, and status tags are the agent's job — so the catalog reflects what
was actually verified, and by whom.
"""

from __future__ import annotations

from pathlib import Path

import yaml
import datahub.metadata.schema_classes as models
from datahub.emitter.mce_builder import (
    make_dataset_urn,
    make_domain_urn,
    make_tag_urn,
    make_user_urn,
)
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.graph.client import DatahubClientConfig, DataHubGraph

PLATFORM = "documents"
PLATFORM_URN = f"urn:li:dataPlatform:{PLATFORM}"
ENV = "PROD"

# Compliance status tags. `unscanned` is applied at ingestion; the agent
# replaces it with a verdict tag after running a real scan.
TAGS = {
    "unscanned": ("Unscanned", "Not yet checked for accessibility", "#9E9E9E"),
    "508-compliant": ("508 Compliant", "Passed all critical automated accessibility checks", "#2E7D32"),
    "508-non-compliant": ("508 Non-Compliant", "Failed one or more critical accessibility checks", "#C62828"),
    "in-remediation": ("In Remediation", "Queued for accessibility remediation", "#F9A825"),
    "public-facing": ("Public-Facing", "Published on the public website", "#1565C0"),
}


def get_graph(server: str = "http://localhost:8080", token: str | None = None) -> DataHubGraph:
    return DataHubGraph(DatahubClientConfig(server=server, token=token))


def document_urn(doc: dict) -> str:
    return make_dataset_urn(PLATFORM, f"rivergate/{doc['id']}", ENV)


def load_manifest(path: str | Path = "corpus/manifest.yaml") -> dict:
    return yaml.safe_load(Path(path).read_text())


def bootstrap_catalog(graph: DataHubGraph, manifest: dict) -> list[str]:
    """Create platform, tags, domains, owners, and document datasets."""
    _emit_platform(graph)
    _emit_tags(graph)
    dept_domains = _emit_departments(graph, manifest["departments"])

    urns = []
    for doc in manifest["documents"]:
        urn = _emit_document(graph, doc, manifest, dept_domains)
        urns.append(urn)

    _emit_lineage(graph, manifest["documents"])
    return urns


# ---------------------------------------------------------------------------


def _emit_platform(graph: DataHubGraph) -> None:
    graph.emit_mcp(
        MetadataChangeProposalWrapper(
            entityUrn=PLATFORM_URN,
            aspect=models.DataPlatformInfoClass(
                name=PLATFORM,
                displayName="Document Library",
                type=models.PlatformTypeClass.OTHERS,
                datasetNameDelimiter="/",
                logoUrl="https://cdn-icons-png.flaticon.com/512/337/337946.png",
            ),
        )
    )


def _emit_tags(graph: DataHubGraph) -> None:
    for tag_id, (name, description, color) in TAGS.items():
        graph.emit_mcp(
            MetadataChangeProposalWrapper(
                entityUrn=make_tag_urn(tag_id),
                aspect=models.TagPropertiesClass(
                    name=name, description=description, colorHex=color
                ),
            )
        )


def _emit_departments(graph: DataHubGraph, departments: dict) -> dict[str, str]:
    """Create one Domain per department and a CorpUser for each owner."""
    domains: dict[str, str] = {}
    for dept_name, info in departments.items():
        domain_urn = make_domain_urn(info["slug"])
        graph.emit_mcp(
            MetadataChangeProposalWrapper(
                entityUrn=domain_urn,
                aspect=models.DomainPropertiesClass(
                    name=dept_name,
                    description=f"{dept_name} department, City of Rivergate",
                ),
            )
        )
        domains[dept_name] = domain_urn

        username = info["owner"].split("@")[0]
        display = username.replace(".", " ").title()
        graph.emit_mcp(
            MetadataChangeProposalWrapper(
                entityUrn=make_user_urn(username),
                aspect=models.CorpUserInfoClass(
                    active=True,
                    displayName=display,
                    email=info["owner"],
                    title=f"{dept_name} — Document Coordinator",
                ),
            )
        )
    return domains


def _emit_document(
    graph: DataHubGraph, doc: dict, manifest: dict, dept_domains: dict[str, str]
) -> str:
    urn = document_urn(doc)
    base_url = manifest["base_url"]
    public_url = f"{base_url}{doc['url_path']}"

    graph.emit_mcp(
        MetadataChangeProposalWrapper(
            entityUrn=urn,
            aspect=models.DatasetPropertiesClass(
                name=doc["title"],
                qualifiedName=f"rivergate/{doc['id']}",
                description=(
                    f"{doc['title']} — published by {doc['department']}, "
                    f"City of Rivergate, on {doc['published']}."
                ),
                externalUrl=public_url if doc["public_facing"] else None,
                customProperties={
                    "documentId": doc["id"],
                    "department": doc["department"],
                    "publicFacing": str(doc["public_facing"]).lower(),
                    "publishedDate": str(doc["published"]),
                    "monthlyViews": str(doc["monthly_views"]),
                    "sourceFile": doc["file"],
                    "format": "PDF",
                },
            ),
        )
    )

    # Document subtype so the UI shows "Document" instead of "Dataset".
    graph.emit_mcp(
        MetadataChangeProposalWrapper(
            entityUrn=urn,
            aspect=models.SubTypesClass(typeNames=["Document"]),
        )
    )

    # Department domain + owner.
    graph.emit_mcp(
        MetadataChangeProposalWrapper(
            entityUrn=urn,
            aspect=models.DomainsClass(domains=[dept_domains[doc["department"]]]),
        )
    )
    owner_email = manifest["departments"][doc["department"]]["owner"]
    graph.emit_mcp(
        MetadataChangeProposalWrapper(
            entityUrn=urn,
            aspect=models.OwnershipClass(
                owners=[
                    models.OwnerClass(
                        owner=make_user_urn(owner_email.split("@")[0]),
                        type=models.OwnershipTypeClass.DATAOWNER,
                    )
                ]
            ),
        )
    )

    # Initial tags: everything starts unscanned; the agent writes verdicts.
    tags = [models.TagAssociationClass(tag=make_tag_urn("unscanned"))]
    if doc["public_facing"]:
        tags.append(models.TagAssociationClass(tag=make_tag_urn("public-facing")))
    graph.emit_mcp(
        MetadataChangeProposalWrapper(
            entityUrn=urn, aspect=models.GlobalTagsClass(tags=tags)
        )
    )

    if doc["public_facing"]:
        graph.emit_mcp(
            MetadataChangeProposalWrapper(
                entityUrn=urn,
                aspect=models.InstitutionalMemoryClass(
                    elements=[
                        models.InstitutionalMemoryMetadataClass(
                            url=public_url,
                            description="Public download page",
                            createStamp=models.AuditStampClass(
                                time=0, actor="urn:li:corpuser:datahub"
                            ),
                        )
                    ]
                ),
            )
        )
    return urn


def _emit_lineage(graph: DataHubGraph, documents: list[dict]) -> None:
    """Original (inaccessible) -> remediated (accessible) dataset lineage."""
    by_id = {d["id"]: d for d in documents}
    for doc in documents:
        source_id = doc.get("remediated_from")
        if not source_id:
            continue
        upstream = document_urn(by_id[source_id])
        downstream = document_urn(doc)
        graph.emit_mcp(
            MetadataChangeProposalWrapper(
                entityUrn=downstream,
                aspect=models.UpstreamLineageClass(
                    upstreams=[
                        models.UpstreamClass(
                            dataset=upstream,
                            type=models.DatasetLineageTypeClass.TRANSFORMED,
                        )
                    ]
                ),
            )
        )
