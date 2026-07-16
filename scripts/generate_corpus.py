#!/usr/bin/env python3
"""Generate the synthetic public-sector PDF corpus for AccessCatalog Agent.

Produces a realistic mix of accessible and inaccessible PDFs for the fictional
City of Rivergate, plus a manifest (corpus/manifest.yaml) describing each
document's department, ownership, public visibility, and remediation lineage.

Document kinds:
  compliant      -- tagged PDF/UA via the WeasyPrint CLI (StructTreeRoot, Title, Lang)
  untagged       -- plain reportlab output: real text layer but no tag structure
  scanned        -- image-only pages (Pillow-rendered) embedded via reportlab
  stripped_meta  -- tagged PDF/UA post-processed with pikepdf to remove Title/Lang
                    (mimics export tools that lose metadata)

Requires: `weasyprint` CLI on PATH (brew install weasyprint), reportlab, pillow,
pikepdf, pyyaml in the active environment.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pikepdf
import yaml
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
PDF_DIR = CORPUS / "pdfs"

MUNICIPALITY = "City of Rivergate"
BASE_URL = "https://rivergate.gov/documents"

DEPARTMENTS = {
    "Public Works": {"owner": "maria.gonzalez@rivergate.gov", "slug": "public-works"},
    "Parks & Recreation": {"owner": "james.okafor@rivergate.gov", "slug": "parks-recreation"},
    "Finance": {"owner": "susan.chen@rivergate.gov", "slug": "finance"},
    "City Clerk": {"owner": "dana.whitfield@rivergate.gov", "slug": "city-clerk"},
    "Health & Human Services": {"owner": "robert.kim@rivergate.gov", "slug": "health-human-services"},
}


@dataclass
class DocSpec:
    doc_id: str
    title: str
    department: str
    kind: str  # compliant | untagged | scanned | stripped_meta
    public_facing: bool
    published: str
    monthly_views: int
    summary: str
    sections: list[tuple[str, list[str]]] = field(default_factory=list)
    remediated_from: str | None = None  # doc_id of the inaccessible original


def _std_sections(topic: str, dept: str) -> list[tuple[str, list[str]]]:
    """Reasonable municipal boilerplate so the PDFs read like real documents."""
    return [
        (
            "Purpose",
            [
                f"This document describes {topic} for residents and staff of the "
                f"{MUNICIPALITY}. It is maintained by the {dept} department and is "
                "reviewed on an annual basis or whenever the underlying policy, "
                "ordinance, or state guidance changes.",
                "Questions about the content of this document should be directed to "
                f"the {dept} front desk during regular business hours, or submitted "
                "through the city's online service portal.",
            ],
        ),
        (
            "Scope and Applicability",
            [
                "The provisions described here apply within the incorporated limits "
                f"of the {MUNICIPALITY} unless otherwise noted. Where state or "
                "federal requirements are stricter, the stricter requirement "
                "governs.",
                "Nothing in this document should be read as legal advice. Residents "
                "with questions about how a requirement applies to their specific "
                "situation are encouraged to contact the department before "
                "beginning work or submitting an application.",
            ],
        ),
        (
            "How to Get Help",
            [
                "Copies of this document are available in alternate formats upon "
                "request, including large print and electronic text. To request an "
                "accommodation, contact the City Clerk's office at least five "
                "business days in advance.",
                f"The latest version of this and other {dept} publications is posted "
                "on the city website. Printed copies available at City Hall may lag "
                "the online version; when in doubt, the online version controls.",
            ],
        ),
    ]


def build_specs() -> list[DocSpec]:
    docs: list[DocSpec] = []

    def add(doc_id, title, dept, kind, public, published, views, topic, remediated_from=None):
        docs.append(
            DocSpec(
                doc_id=doc_id,
                title=title,
                department=dept,
                kind=kind,
                public_facing=public,
                published=published,
                monthly_views=views,
                summary=f"{title} — {dept}, {MUNICIPALITY}.",
                sections=_std_sections(topic, dept),
                remediated_from=remediated_from,
            )
        )

    # ---- Public Works (5) ----
    add("pw-row-permit-guide", "Right-of-Way Permit Application Guide", "Public Works",
        "untagged", True, "2025-11-03", 1840, "how to apply for a right-of-way construction permit")
    add("pw-standard-details-2026", "Standard Construction Details 2026", "Public Works",
        "compliant", True, "2026-01-15", 960, "the city's standard engineering construction details")
    add("pw-snow-plan", "Snow and Ice Response Plan", "Public Works",
        "scanned", True, "2024-10-20", 2210, "snow plowing priorities and ice response operations")
    add("pw-fleet-policy", "Fleet Vehicle Use Policy", "Public Works",
        "untagged", False, "2025-06-11", 45, "employee use of city fleet vehicles")
    add("pw-stormwater-bmp", "Stormwater BMP Maintenance Handbook", "Public Works",
        "stripped_meta", True, "2025-08-29", 530, "maintenance of stormwater best management practices")

    # ---- Parks & Recreation (4) ----
    add("pr-shelter-rental", "Park Shelter Rental Rules and Fees", "Parks & Recreation",
        "untagged", True, "2026-02-01", 3120, "reserving park shelters and associated fees")
    add("pr-summer-programs", "Summer Recreation Program Catalog 2026", "Parks & Recreation",
        "compliant", True, "2026-04-15", 4480, "summer recreation programs, camps, and registration")
    add("pr-tree-ordinance", "Street Tree Ordinance Summary", "Parks & Recreation",
        "scanned", True, "2023-05-08", 380, "the street tree planting and removal ordinance")
    add("pr-volunteer-handbook", "Volunteer Coach Handbook", "Parks & Recreation",
        "untagged", False, "2025-09-30", 85, "expectations and safety rules for volunteer coaches")

    # ---- Finance (5, incl. remediation pair) ----
    add("fin-budget-2026", "Adopted Budget Fiscal Year 2026", "Finance",
        "untagged", True, "2025-12-18", 1520, "the adopted city budget for fiscal year 2026")
    add("fin-budget-2026-remediated", "Adopted Budget Fiscal Year 2026 (Accessible Edition)", "Finance",
        "compliant", True, "2026-03-02", 640, "the adopted city budget for fiscal year 2026",
        remediated_from="fin-budget-2026")
    add("fin-vendor-w9-guide", "Vendor Registration and W-9 Submission Guide", "Finance",
        "untagged", True, "2025-07-22", 890, "registering as a city vendor and submitting tax forms")
    add("fin-acfr-2025", "Annual Comprehensive Financial Report 2025", "Finance",
        "stripped_meta", True, "2026-05-30", 410, "the audited annual comprehensive financial report")
    add("fin-pcard-policy", "Purchasing Card Internal Policy", "Finance",
        "untagged", False, "2024-11-05", 30, "employee purchasing card rules and reconciliation")

    # ---- City Clerk (4, incl. remediation pair) ----
    add("clk-council-minutes-jun", "City Council Meeting Minutes — June 2026", "City Clerk",
        "scanned", True, "2026-07-01", 760, "official minutes of the June city council meetings")
    add("clk-council-minutes-jun-remediated", "City Council Meeting Minutes — June 2026 (Accessible Edition)", "City Clerk",
        "compliant", True, "2026-07-10", 210, "official minutes of the June city council meetings",
        remediated_from="clk-council-minutes-jun")
    add("clk-public-records-guide", "Public Records Request Guide", "City Clerk",
        "compliant", True, "2026-01-08", 1130, "how to submit and track a public records request")
    add("clk-election-poll-worker", "Election Poll Worker Manual", "City Clerk",
        "untagged", True, "2026-06-12", 540, "duties and procedures for election poll workers")

    # ---- Health & Human Services (4) ----
    add("hhs-food-permit", "Mobile Food Vendor Permit Requirements", "Health & Human Services",
        "untagged", True, "2025-10-14", 1660, "health permits for mobile food vendors and food trucks")
    add("hhs-inspection-checklist", "Restaurant Inspection Self-Audit Checklist", "Health & Human Services",
        "stripped_meta", True, "2025-03-19", 720, "the self-audit checklist used before health inspections")
    add("hhs-assistance-programs", "Emergency Assistance Programs Overview", "Health & Human Services",
        "compliant", True, "2026-02-20", 2050, "emergency rent, utility, and food assistance programs")
    add("hhs-staff-bbp-plan", "Bloodborne Pathogen Exposure Control Plan", "Health & Human Services",
        "untagged", False, "2025-01-27", 20, "staff exposure control procedures for bloodborne pathogens")

    return docs


# --------------------------------------------------------------------------
# Renderers
# --------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  @page {{ size: Letter; margin: 1in; }}
  body {{ font-family: Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #1a1a1a; }}
  header {{ border-bottom: 3px solid #14417b; margin-bottom: 1.5em; padding-bottom: 0.5em; }}
  .agency {{ color: #14417b; font-size: 9pt; letter-spacing: 0.1em; text-transform: uppercase; }}
  h1 {{ font-size: 20pt; margin: 0.2em 0; }}
  h2 {{ font-size: 13pt; color: #14417b; margin-top: 1.4em; }}
  .meta {{ font-size: 9pt; color: #555; }}
  table {{ border-collapse: collapse; margin: 1em 0; width: 100%; }}
  th, td {{ border: 1px solid #999; padding: 6px 10px; text-align: left; font-size: 10pt; }}
  th {{ background: #e8eef7; }}
  footer {{ margin-top: 2em; font-size: 8pt; color: #777; }}
</style>
</head>
<body>
<header>
  <div class="agency">{municipality} &mdash; {department}</div>
  <h1>{title}</h1>
  <div class="meta">Published {published} &middot; Document ID {doc_id}</div>
</header>
{body}
<h2>Contact Reference</h2>
<table>
  <tr><th>Department</th><th>Responsible Office</th><th>Phone</th></tr>
  <tr><td>{department}</td><td>City Hall, 200 River Street</td><td>(555) 010-4400</td></tr>
</table>
<footer>{municipality} &middot; This document is provided for public information purposes.</footer>
</body>
</html>
"""


def render_compliant(spec: DocSpec, out_path: Path) -> None:
    """Tagged PDF/UA via the WeasyPrint CLI: StructTreeRoot, Marked, Title, Lang."""
    body = []
    for heading, paras in spec.sections:
        body.append(f"<h2>{heading}</h2>")
        body.extend(f"<p>{p}</p>" for p in paras)
    html = HTML_TEMPLATE.format(
        title=spec.title,
        municipality=MUNICIPALITY,
        department=spec.department,
        published=spec.published,
        doc_id=spec.doc_id,
        body="\n".join(body),
    )
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
        html_path = f.name
    subprocess.run(
        ["weasyprint", "--pdf-variant", "pdf/ua-1", html_path, str(out_path)],
        check=True,
        capture_output=True,
    )
    Path(html_path).unlink()


def render_untagged(spec: DocSpec, out_path: Path) -> None:
    """Plain reportlab output: selectable text, but no tags, no Lang, no title."""
    c = canvas.Canvas(str(out_path), pagesize=LETTER)
    width, height = LETTER
    y = height - 1 * inch
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, y, spec.title[:70])
    y -= 0.3 * inch
    c.setFont("Helvetica", 9)
    c.drawString(1 * inch, y, f"{MUNICIPALITY} — {spec.department} — Published {spec.published}")
    y -= 0.5 * inch
    for heading, paras in spec.sections:
        if y < 2 * inch:
            c.showPage()
            y = height - 1 * inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, y, heading)
        y -= 0.25 * inch
        c.setFont("Helvetica", 10)
        for para in paras:
            for line in _wrap(para, 88):
                if y < 1 * inch:
                    c.showPage()
                    y = height - 1 * inch
                    c.setFont("Helvetica", 10)
                c.drawString(1 * inch, y, line)
                y -= 0.18 * inch
            y -= 0.12 * inch
    c.save()


def render_scanned(spec: DocSpec, out_path: Path) -> None:
    """Image-only pages: text rendered to a bitmap, embedded with no text layer."""
    img = Image.new("RGB", (1700, 2200), "#f7f5f0")  # slightly off-white like a scan
    draw = ImageDraw.Draw(img)
    try:
        font_h = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 44)
        font_b = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
    except OSError:
        font_h = ImageFont.load_default()
        font_b = font_h
    y = 140
    draw.text((150, y), spec.title[:60], fill="#222", font=font_h)
    y += 90
    draw.text((150, y), f"{MUNICIPALITY} — {spec.department}", fill="#444", font=font_b)
    y += 80
    for heading, paras in spec.sections:
        draw.text((150, y), heading.upper(), fill="#222", font=font_b)
        y += 50
        for para in paras:
            for line in _wrap(para, 90):
                draw.text((150, y), line, fill="#333", font=font_b)
                y += 38
                if y > 2050:
                    break
            y += 14
            if y > 2050:
                break
        y += 20
        if y > 2050:
            break
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img.save(f.name, "PNG")
        png_path = f.name
    c = canvas.Canvas(str(out_path), pagesize=LETTER)
    c.drawImage(png_path, 0, 0, width=LETTER[0], height=LETTER[1])
    c.showPage()
    c.save()
    Path(png_path).unlink()


def render_stripped_meta(spec: DocSpec, out_path: Path) -> None:
    """Tagged PDF that lost its Title and Lang (a common real-world export bug)."""
    render_compliant(spec, out_path)
    with pikepdf.open(out_path, allow_overwriting_input=True) as pdf:
        if "/Lang" in pdf.Root:
            del pdf.Root["/Lang"]
        with pdf.open_metadata() as meta:
            meta["dc:title"] = ""
        if pdf.docinfo is not None and "/Title" in pdf.docinfo:
            del pdf.docinfo["/Title"]
        pdf.save()


def _wrap(text: str, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


RENDERERS = {
    "compliant": render_compliant,
    "untagged": render_untagged,
    "scanned": render_scanned,
    "stripped_meta": render_stripped_meta,
}


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    if shutil.which("weasyprint") is None:
        sys.exit("weasyprint CLI not found — install with `brew install weasyprint`")

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    specs = build_specs()

    manifest_docs = []
    for spec in specs:
        out_path = PDF_DIR / f"{spec.doc_id}.pdf"
        RENDERERS[spec.kind](spec, out_path)
        dept_slug = DEPARTMENTS[spec.department]["slug"]
        manifest_docs.append(
            {
                "id": spec.doc_id,
                "title": spec.title,
                "department": spec.department,
                "public_facing": spec.public_facing,
                "url_path": f"/{dept_slug}/{spec.doc_id}.pdf",
                "file": str(out_path.relative_to(ROOT)),
                "published": spec.published,
                "monthly_views": spec.monthly_views,
                "remediated_from": spec.remediated_from,
            }
        )
        print(f"  [{spec.kind:>13}] {out_path.name}")

    manifest = {
        "municipality": MUNICIPALITY,
        "base_url": BASE_URL,
        "departments": {
            name: {"owner": info["owner"], "slug": info["slug"]}
            for name, info in DEPARTMENTS.items()
        },
        "documents": manifest_docs,
    }
    manifest_path = CORPUS / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
    print(f"\nWrote {len(manifest_docs)} documents and {manifest_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
