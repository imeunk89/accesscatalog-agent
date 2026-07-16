"""Real PDF accessibility checks, mapped to Section 508 / WCAG criteria.

These are the automated first-pass checks an accessibility practitioner runs
before manual review: tag structure, document title, language, image-only
(scanned) pages, bookmarks, and form field labels. Automated checks cannot
prove a PDF is fully accessible, but they reliably prove many PDFs are NOT —
which is exactly what a remediation queue needs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import pikepdf
from pypdf import PdfReader

# Titles that count as "no meaningful title" — reportlab and various export
# tools stamp these defaults on documents whose authors never set one.
MEANINGLESS_TITLES = {"", "untitled", "anonymous", "document", "microsoft word"}

#: A page with fewer extracted characters than this, but containing an image
#: XObject, is treated as image-only (i.e. a scan with no text layer).
IMAGE_ONLY_TEXT_THRESHOLD = 20

#: Documents longer than this should offer bookmarks for navigation.
BOOKMARK_PAGE_THRESHOLD = 10


@dataclass
class CheckResult:
    check_id: str
    name: str
    passed: bool
    severity: str  # "critical" | "warning"
    standard: str  # Section 508 / WCAG mapping
    detail: str


@dataclass
class ScanResult:
    file: str
    page_count: int
    compliant: bool
    critical_failures: int
    warnings: int
    score: int  # 0-100, weighted pass ratio
    checks: list[CheckResult] = field(default_factory=list)

    def failed_checks(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed]

    def to_dict(self) -> dict:
        return asdict(self)


def scan(path: str | Path) -> ScanResult:
    """Run all accessibility checks against a single PDF."""
    path = Path(path)
    checks: list[CheckResult] = []

    with pikepdf.open(path) as pdf:
        root = pdf.Root
        page_count = len(pdf.pages)

        # -- 1. Tag structure (WCAG 1.3.1 Info and Relationships) ------------
        has_struct_tree = "/StructTreeRoot" in root
        marked = False
        if "/MarkInfo" in root:
            marked = bool(root.MarkInfo.get("/Marked", False))
        checks.append(
            CheckResult(
                check_id="tagged-pdf",
                name="Tagged PDF structure",
                passed=has_struct_tree and marked,
                severity="critical",
                standard="Section 508 E205 / WCAG 1.3.1",
                detail=(
                    "Document has a structure tree and is marked as tagged."
                    if has_struct_tree and marked
                    else "No tag structure: screen readers cannot determine "
                    "headings, tables, or reading order."
                ),
            )
        )

        # -- 2. Document title (WCAG 2.4.2 Page Titled) -----------------------
        info_title = str(pdf.docinfo.get("/Title", "")).strip() if pdf.docinfo else ""
        with pdf.open_metadata() as meta:
            xmp_title = (meta.get("dc:title") or "").strip()
        title = xmp_title or info_title
        has_title = title.lower() not in MEANINGLESS_TITLES
        checks.append(
            CheckResult(
                check_id="doc-title",
                name="Document title",
                passed=has_title,
                severity="critical",
                standard="Section 508 E205 / WCAG 2.4.2",
                detail=(
                    f"Title present: {title!r}."
                    if has_title
                    else f"No meaningful document title (found {title!r})."
                ),
            )
        )

        # -- 3. Primary language (WCAG 3.1.1 Language of Page) ----------------
        lang = str(root.get("/Lang", "")).strip()
        checks.append(
            CheckResult(
                check_id="doc-language",
                name="Primary language declared",
                passed=bool(lang),
                severity="critical",
                standard="Section 508 E205 / WCAG 3.1.1",
                detail=(
                    f"Language declared: {lang!r}."
                    if lang
                    else "No /Lang entry: screen readers cannot pick the "
                    "correct speech synthesizer language."
                ),
            )
        )

        # -- 4. Form field labels (WCAG 3.3.2 Labels or Instructions) --------
        form_fields = []
        acro = root.get("/AcroForm")
        if acro is not None and "/Fields" in acro:
            form_fields = list(acro.Fields)
        if form_fields:
            unlabeled = sum(1 for f in form_fields if "/TU" not in f)
            checks.append(
                CheckResult(
                    check_id="form-labels",
                    name="Form field labels",
                    passed=unlabeled == 0,
                    severity="critical",
                    standard="Section 508 E205 / WCAG 3.3.2",
                    detail=(
                        f"All {len(form_fields)} form fields have tooltips."
                        if unlabeled == 0
                        else f"{unlabeled} of {len(form_fields)} form fields "
                        "have no accessible label (/TU tooltip)."
                    ),
                )
            )

        # -- 5. Bookmarks for long documents (WCAG 2.4.5 Multiple Ways) ------
        has_outline = "/Outlines" in root and root.Outlines.get("/Count", 0) != 0
        if page_count > BOOKMARK_PAGE_THRESHOLD:
            checks.append(
                CheckResult(
                    check_id="bookmarks",
                    name="Bookmarks in long document",
                    passed=bool(has_outline),
                    severity="warning",
                    standard="WCAG 2.4.5 (best practice)",
                    detail=(
                        "Document provides bookmarks."
                        if has_outline
                        else f"{page_count}-page document has no bookmarks."
                    ),
                )
            )

        # -- 6. Display document title in window bar (supports WCAG 2.4.2) ---
        prefs = root.get("/ViewerPreferences")
        display_title = bool(prefs is not None and prefs.get("/DisplayDocTitle", False))
        checks.append(
            CheckResult(
                check_id="display-doc-title",
                name="Window title shows document title",
                passed=display_title,
                severity="warning",
                standard="PDF/UA-1 / supports WCAG 2.4.2",
                detail=(
                    "Viewer is configured to display the document title."
                    if display_title
                    else "Viewer shows the filename instead of the title."
                ),
            )
        )

    # -- 7. Image-only pages / missing text layer (WCAG 1.1.1 & 1.4.5) -------
    image_only_pages = _find_image_only_pages(path)
    checks.append(
        CheckResult(
            check_id="text-layer",
            name="Real text layer (not a scan)",
            passed=not image_only_pages,
            severity="critical",
            standard="Section 508 E205 / WCAG 1.1.1, 1.4.5",
            detail=(
                "All pages contain extractable text."
                if not image_only_pages
                else f"Image-only pages with no text layer: "
                f"{_page_list(image_only_pages)}. Likely an untreated scan."
            ),
        )
    )

    critical_failures = sum(1 for c in checks if not c.passed and c.severity == "critical")
    warnings = sum(1 for c in checks if not c.passed and c.severity == "warning")
    # Weighted score: critical checks worth 3x a warning.
    total_weight = sum(3 if c.severity == "critical" else 1 for c in checks)
    passed_weight = sum(
        (3 if c.severity == "critical" else 1) for c in checks if c.passed
    )
    return ScanResult(
        file=str(path),
        page_count=page_count,
        compliant=critical_failures == 0,
        critical_failures=critical_failures,
        warnings=warnings,
        score=round(100 * passed_weight / total_weight),
        checks=checks,
    )


def _find_image_only_pages(path: Path) -> list[int]:
    """Pages that contain an image XObject but effectively no extractable text."""
    reader = PdfReader(str(path))
    image_only = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception:  # malformed content stream — treat as no text
            text = ""
        if len(text) >= IMAGE_ONLY_TEXT_THRESHOLD:
            continue
        resources = page.get("/Resources") or {}
        xobjects = resources.get("/XObject") or {}
        has_image = any(
            xobjects[name].get("/Subtype") == "/Image" for name in xobjects
        )
        if has_image:
            image_only.append(i)
    return image_only


def _page_list(pages: list[int], limit: int = 5) -> str:
    shown = ", ".join(str(p) for p in pages[:limit])
    return shown + (f" (+{len(pages) - limit} more)" if len(pages) > limit else "")
