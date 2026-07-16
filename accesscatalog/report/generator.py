"""Compliance report generation.

Reports are built from LIVE DataHub catalog state — tags, custom properties,
ownership, and lineage — not from local files. If it isn't in the catalog,
it isn't in the report. That's the point: the catalog is the system of
record that people and agents share.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import datahub.metadata.schema_classes as models
from datahub.ingestion.graph.client import DataHubGraph

from accesscatalog.ingest import get_graph

PLATFORM = "documents"

STATUS_ORDER = ["508-non-compliant", "in-remediation", "unscanned", "508-compliant"]
STATUS_LABEL = {
    "508-compliant": "Compliant",
    "508-non-compliant": "Non-compliant",
    "in-remediation": "In remediation",
    "unscanned": "Unscanned",
}


def collect_catalog_state(server: str = "http://localhost:8080") -> dict:
    graph = get_graph(server)
    urns = list(
        graph.get_urns_by_filter(platform=PLATFORM, entity_types=["dataset"])
    )

    docs: list[dict] = []
    owners_by_dept: dict[str, str] = {}
    for urn in urns:
        props = graph.get_aspect(urn, models.DatasetPropertiesClass)
        if props is None:
            continue
        tags_aspect = graph.get_aspect(urn, models.GlobalTagsClass)
        tag_ids = {t.tag.split(":")[-1] for t in (tags_aspect.tags if tags_aspect else [])}
        status = next((s for s in STATUS_ORDER if s in tag_ids), "unscanned")

        ownership = graph.get_aspect(urn, models.OwnershipClass)
        owner = (
            ownership.owners[0].owner.split(":")[-1] if ownership and ownership.owners else ""
        )
        upstream = graph.get_aspect(urn, models.UpstreamLineageClass)
        remediates = (
            upstream.upstreams[0].dataset if upstream and upstream.upstreams else None
        )

        cp = props.customProperties
        dept = cp.get("department", "Unknown")
        if owner:
            owners_by_dept.setdefault(dept, owner)
        docs.append(
            {
                "urn": urn,
                "id": cp.get("documentId", urn.split("/")[-1].split(",")[0]),
                "title": props.name,
                "department": dept,
                "status": status,
                "public_facing": cp.get("publicFacing") == "true",
                "monthly_views": int(cp.get("monthlyViews", 0)),
                "score": int(cp["accessibilityScore"]) if "accessibilityScore" in cp else None,
                "failed_checks": cp.get("failedChecks", ""),
                "queue_position": int(cp["remediationQueuePosition"])
                if "remediationQueuePosition" in cp
                else None,
                "last_scanned": cp.get("lastScannedAt", ""),
                "remediates_urn": remediates,
                "owner": owner,
            }
        )

    # Documents that HAVE an accessible downstream edition (redirect candidates).
    remediated_sources = {d["remediates_urn"] for d in docs if d["remediates_urn"]}
    for d in docs:
        d["has_accessible_edition"] = d["urn"] in remediated_sources

    departments: dict[str, dict] = {}
    for d in sorted(docs, key=lambda x: x["department"]):
        row = departments.setdefault(
            d["department"],
            {
                "total": 0,
                "compliant": 0,
                "non_compliant": 0,
                "in_remediation": 0,
                "unscanned": 0,
                "owner": owners_by_dept.get(d["department"], ""),
            },
        )
        row["total"] += 1
        key = {
            "508-compliant": "compliant",
            "508-non-compliant": "non_compliant",
            "in-remediation": "in_remediation",
            "unscanned": "unscanned",
        }[d["status"]]
        row[key] += 1

    return {
        "municipality": "City of Rivergate",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "server": server,
        "documents": sorted(docs, key=lambda x: (x["department"], x["id"])),
        "departments": departments,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def generate_reports(server: str, out_dir: Path) -> list[Path]:
    state = collect_catalog_state(server)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "compliance_report.md"
    html_path = out_dir / "compliance_report.html"
    md_path.write_text(render_markdown(state))
    html_path.write_text(render_html(state))
    return [md_path, html_path]


def render_markdown(state: dict) -> str:
    docs = state["documents"]
    public = [d for d in docs if d["public_facing"]]
    scanned = [d for d in docs if d["status"] != "unscanned"]
    non_compliant = [d for d in docs if d["status"] in ("508-non-compliant", "in-remediation")]
    queued = sorted(
        (d for d in docs if d["queue_position"] is not None),
        key=lambda d: d["queue_position"],
    )
    redirects = [d for d in docs if d["has_accessible_edition"] and d["status"] != "508-compliant"]

    lines = [
        f"# {state['municipality']} — Document Accessibility Compliance Report",
        "",
        f"*Generated {state['generated_at']} from DataHub catalog state ({state['server']})*",
        "",
        "## Executive summary",
        "",
        f"- **{len(docs)}** documents in the catalog ({len(public)} public-facing)",
        f"- **{len(scanned)}** scanned; **{len(non_compliant)}** currently non-compliant",
        f"- **{len(queued)}** documents in the remediation queue",
        f"- **{len(redirects)}** documents already have an accessible edition "
        "(redirect the public URL instead of re-remediating)",
        "",
        "## Compliance by department",
        "",
        "| Department | Owner | Docs | Compliant | Non-compliant | In remediation | Unscanned |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for dept, row in state["departments"].items():
        lines.append(
            f"| {dept} | {row['owner']} | {row['total']} | {row['compliant']} | "
            f"{row['non_compliant']} | {row['in_remediation']} | {row['unscanned']} |"
        )

    if queued:
        lines += [
            "",
            "## Remediation queue (public-facing, priority order)",
            "",
            "| # | Document | Department | Monthly views | Score | Failed checks |",
            "|---:|---|---|---:|---:|---|",
        ]
        for d in queued:
            lines.append(
                f"| {d['queue_position']} | {d['title']} | {d['department']} | "
                f"{d['monthly_views']:,} | {d['score']} | {d['failed_checks']} |"
            )

    if redirects:
        lines += [
            "",
            "## Redirect recommendations (accessible edition already exists)",
            "",
        ]
        for d in redirects:
            lines.append(
                f"- **{d['title']}** ({d['department']}) — an accessible edition is "
                "already published; point the public URL at it and archive this file."
            )

    lines += [
        "",
        "## Full inventory",
        "",
        "| Document | Department | Public | Status | Score | Last scanned |",
        "|---|---|---|---|---:|---|",
    ]
    for d in docs:
        lines.append(
            f"| {d['title']} | {d['department']} | {'yes' if d['public_facing'] else 'no'} | "
            f"{STATUS_LABEL[d['status']]} | {d['score'] if d['score'] is not None else '—'} | "
            f"{d['last_scanned'] or '—'} |"
        )
    lines += [
        "",
        "---",
        "*Produced by AccessCatalog Agent. Status tags, scan evidence, ownership, "
        "and lineage all live in DataHub — this report is a view, not a silo.*",
        "",
    ]
    return "\n".join(lines)


HTML_STYLE = """
:root { color-scheme: light; }
html { background: #ffffff; }
body { font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
       max-width: 960px; margin: 2rem auto; padding: 0 1rem; color: #1a1a2e;
       background: #ffffff; line-height: 1.55; }
h1 { border-bottom: 3px solid #14417b; padding-bottom: .4rem; }
h2 { color: #14417b; margin-top: 2rem; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: .92rem; }
th, td { border: 1px solid #d0d7e2; padding: .45rem .6rem; text-align: left; }
th { background: #e8eef7; }
tr:nth-child(even) td { background: #f7f9fc; }
.badge { display: inline-block; padding: .1rem .55rem; border-radius: 999px;
         font-size: .8rem; font-weight: 600; color: #fff; }
.b-compliant { background: #2E7D32; } .b-non-compliant { background: #C62828; }
.b-in-remediation { background: #F9A825; color: #333; } .b-unscanned { background: #9E9E9E; }
.kpis { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1.2rem 0; }
.kpi { flex: 1 1 150px; background: #f0f4fa; border-radius: 10px; padding: .9rem 1rem; }
.kpi b { display: block; font-size: 1.7rem; color: #14417b; }
footer { margin-top: 2.5rem; font-size: .8rem; color: #667; }
"""

BADGE_CLASS = {
    "508-compliant": "b-compliant",
    "508-non-compliant": "b-non-compliant",
    "in-remediation": "b-in-remediation",
    "unscanned": "b-unscanned",
}


def render_html(state: dict) -> str:
    docs = state["documents"]
    public = [d for d in docs if d["public_facing"]]
    non_compliant = [d for d in docs if d["status"] in ("508-non-compliant", "in-remediation")]
    queued = sorted(
        (d for d in docs if d["queue_position"] is not None),
        key=lambda d: d["queue_position"],
    )
    redirects = [d for d in docs if d["has_accessible_edition"] and d["status"] != "508-compliant"]

    def badge(status: str) -> str:
        return f'<span class="badge {BADGE_CLASS[status]}">{STATUS_LABEL[status]}</span>'

    dept_rows = "".join(
        f"<tr><td>{dept}</td><td>{row['owner']}</td><td>{row['total']}</td>"
        f"<td>{row['compliant']}</td><td>{row['non_compliant']}</td>"
        f"<td>{row['in_remediation']}</td><td>{row['unscanned']}</td></tr>"
        for dept, row in state["departments"].items()
    )
    queue_rows = "".join(
        f"<tr><td>{d['queue_position']}</td><td>{d['title']}</td><td>{d['department']}</td>"
        f"<td>{d['monthly_views']:,}</td><td>{d['score']}</td><td>{d['failed_checks']}</td></tr>"
        for d in queued
    )
    redirect_items = "".join(
        f"<li><b>{d['title']}</b> ({d['department']}) — accessible edition already "
        "published; redirect the public URL and archive this file.</li>"
        for d in redirects
    )
    inventory_rows = "".join(
        f"<tr><td>{d['title']}</td><td>{d['department']}</td>"
        f"<td>{'yes' if d['public_facing'] else 'no'}</td><td>{badge(d['status'])}</td>"
        f"<td>{d['score'] if d['score'] is not None else '—'}</td></tr>"
        for d in docs
    )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{state['municipality']} — Accessibility Compliance Report</title>
<style>{HTML_STYLE}</style></head><body>
<h1>{state['municipality']} — Document Accessibility Compliance</h1>
<p><em>Generated {state['generated_at']} from live DataHub catalog state.</em></p>
<div class="kpis">
  <div class="kpi"><b>{len(docs)}</b>documents cataloged</div>
  <div class="kpi"><b>{len(public)}</b>public-facing</div>
  <div class="kpi"><b>{len(non_compliant)}</b>non-compliant</div>
  <div class="kpi"><b>{len(queued)}</b>in remediation queue</div>
</div>
<h2>Compliance by department</h2>
<table><tr><th>Department</th><th>Owner</th><th>Docs</th><th>Compliant</th>
<th>Non-compliant</th><th>In remediation</th><th>Unscanned</th></tr>{dept_rows}</table>
{'<h2>Remediation queue</h2><table><tr><th>#</th><th>Document</th><th>Department</th><th>Monthly views</th><th>Score</th><th>Failed checks</th></tr>' + queue_rows + '</table>' if queued else ''}
{'<h2>Redirect recommendations</h2><ul>' + redirect_items + '</ul>' if redirects else ''}
<h2>Full inventory</h2>
<table><tr><th>Document</th><th>Department</th><th>Public</th><th>Status</th>
<th>Score</th></tr>{inventory_rows}</table>
<footer>Produced by AccessCatalog Agent — status tags, scan evidence, ownership,
and lineage live in DataHub; this report is a view, not a silo.</footer>
</body></html>
"""
