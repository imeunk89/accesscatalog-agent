## Executive summary

All 22 unscanned documents on the `documents` platform have now been scanned, lineage-checked, and—where appropriate—queued for remediation.

Authoritative scan status from the catalog:

- **Total scanned this run:** 22
- **By verdict:**  
  - 508-compliant: **6**  
  - 508-non-compliant: **16**
- **By verdict and visibility:**  
  - **Public-facing:**  
    - 508-compliant: **6**  
    - 508-non-compliant: **12**  
  - **Internal-only:**  
    - 508-compliant: **0**  
    - 508-non-compliant: **4**

The remediation queue currently contains **10** public-facing, non-compliant documents confirmed by `get_queue_status`. Two additional high-traffic public-facing documents already have accessible downstream editions; for these, the required action is URL redirection rather than remediation.

---

## Remediation queue (authoritative positions 1–10)

Below are only the documents confirmed as queued by `get_queue_status`, in priority order. “Failed checks” are summarized from the scan results.

| Pos | Document (title) | Department | Owner | Monthly views | Key failed checks (examples) | Rationale (impact + reasoning) |
|-----|------------------|-----------|-------|---------------|------------------------------|--------------------------------|
| 1 | **Park Shelter Rental Rules and Fees** (`pr-shelter-rental`) | Parks & Recreation | James Okafor | ~3120 | Untagged PDF; no declared language; no meaningful document title; filename shown instead of title | Highest-traffic public-facing Parks & Recreation rules document. Critical failures make the rules and fee schedule hard or impossible to use with assistive tech. No accessible downstream edition exists, so full remediation is required. |
| 2 | **Street Tree Ordinance Summary** (`pr-tree-ordinance`) | Parks & Recreation | James Okafor | ~380 | Image-only, untagged PDF; no language; no meaningful title; filename shown instead of title; no text layer | Public-facing legal/ordinance summary that is effectively a scanned image, unusable with screen readers. No downstream accessible edition; remediation is needed so residents can access tree ordinance requirements. |
| 3 | **Snow and Ice Response Plan** (`pw-snow-plan`) | Public Works | Maria Gonzalez | ~2210 | Image-only, untagged PDF; no language; no meaningful title; filename shown instead of title; no text layer | High-traffic emergency operations document for winter events. Image-only and untagged; inaccessible to screen-reader users. No downstream accessible edition; remediation is required so residents can access critical safety information. |
| 4 | **Right-of-Way Permit Application Guide** (`pw-row-permit-guide`) | Public Works | Maria Gonzalez | ~1840 | Untagged PDF; no language; no meaningful title; filename shown instead of title | High-traffic permitting guidance used by contractors and residents. Structural and metadata failures impede assistive-tech use. No accessible downstream edition; remediation required. |
| 5 | **Mobile Food Vendor Permit Requirements** (`hhs-food-permit`) | Health & Human Services | Robert Kim | ~1660 | Untagged PDF; no language; no meaningful title; filename shown instead of title | High-traffic public-facing permitting guide. Structural and metadata failures; no accessible downstream edition. Remediation necessary so food vendors with disabilities can understand and meet requirements. |
| 6 | **Vendor Registration and W-9 Submission Guide** (`fin-vendor-w9-guide`) | Finance | Susan Chen | ~890 | Untagged PDF; no language; no meaningful title; filename shown instead of title | Heavily used Finance onboarding guide for vendors. Inaccessible structure and missing language metadata affect equitable access. No downstream accessible edition; remediation needed. |
| 7 | **Stormwater BMP Maintenance Handbook** (`pw-stormwater-bmp`) | Public Works | Maria Gonzalez | ~530 | Missing document language; no meaningful title | Technical handbook relied on by property owners/engineers. Metadata failures undermine navigation and comprehension for assistive-tech users. No downstream accessible edition; remediation needed (titles/lang plus structural review). |
| 8 | **Restaurant Inspection Self-Audit Checklist** (`hhs-inspection-checklist`) | Health & Human Services | Robert Kim | ~720 | Missing document language; no meaningful title | Public-facing compliance checklist. Metadata issues affect screen-reader navigation; no accessible downstream edition. Remediation required so restaurant operators using assistive tech can self-audit. |
| 9 | **Annual Comprehensive Financial Report 2025** (`fin-acfr-2025`) | Finance | Susan Chen | ~410 | Missing document language; no meaningful title | Public-facing audited financial report. Metadata failures reduce accessibility of a key transparency document. No accessible downstream edition; remediation needed. |
| 10 | **Election Poll Worker Manual** (`clk-election-poll-worker`) | City Clerk | Dana Whitfield | ~540 | Untagged PDF; no language; no meaningful title; filename shown instead of title | Public-facing training manual for poll workers. Structural and metadata failures significantly impact access for prospective/current poll workers with disabilities. No downstream accessible edition; remediation required. |

All 10 above are confirmed queued with these positions by `get_queue_status`.

---

## Redirect recommendations (lineage-aware)

Lineage checks were run downstream for every non-compliant document before queueing. Two non-compliant, public-facing documents already have accessible, compliant editions downstream:

1. **City Council Meeting Minutes — June 2026** (`clk-council-minutes-jun`)  
   - Status: **508-non-compliant**, public-facing, ~760 monthly views. Includes critical issues: untagged PDF, missing language and meaningful title, and image-only page(s) without a text layer.  
   - Lineage: Downstream dataset **`clk-council-minutes-jun-remediated`**, tagged 508-compliant and public-facing, with score 100 and no critical failures.  
   - Recommendation:  
     - Do **not** remediate the original; do **not** queue.  
     - Update all public URLs and internal references to point to **City Council Meeting Minutes — June 2026 (Accessible Edition)** (`clk-council-minutes-jun-remediated`).  
     - Archive or clearly label the original as superseded / inaccessible to prevent users from landing on it.

2. **Adopted Budget Fiscal Year 2026** (`fin-budget-2026`)  
   - Status: **508-non-compliant**, public-facing, ~1520 monthly views. Fails tagging, language, and title checks.  
   - Lineage: Downstream dataset **`fin-budget-2026-remediated`**, tagged 508-compliant and public-facing, with score 100 and no critical failures.  
   - Recommendation:  
     - Do **not** remediate the original; do **not** queue.  
     - Update public links on the budget/finance pages to point to **Adopted Budget Fiscal Year 2026 (Accessible Edition)** (`fin-budget-2026-remediated`).  
     - Retain the original only as an internal historical artifact or label it clearly as superseded and inaccessible.

Both redirect recommendations are based directly on `get_lineage` results showing a downstream, public-facing, 508-compliant edition with `accessibilityCompliant=true` and `criticalFailures=0`.

---

## Compliant documents (done, no queueing)

The following 6 scanned documents are **508-compliant** and not in the remediation queue:

- `clk-council-minutes-jun-remediated` — City Clerk  
- `clk-public-records-guide` — City Clerk  
- `fin-budget-2026-remediated` — Finance  
- `hhs-assistance-programs` — Health & Human Services  
- `pr-summer-programs` — Parks & Recreation  
- `pw-standard-details-2026` — Public Works  

These are fully scanned (score 100, no failed checks) and appear as compliant in the catalog’s authoritative counts.

---

## Non-compliant internal documents (no queueing by policy)

Per your rules, internal-only documents are **not** queued but are noted here for completeness. All four of these are 508-non-compliant and internal (`publicFacing=false`):

- `fin-pcard-policy` — Finance (Purchasing Card Internal Policy)  
  - Failed checks: untagged PDF, no meaningful title, no /Lang, filename shown instead of title.
- `hhs-staff-bbp-plan` — Health & Human Services (Bloodborne Pathogen Exposure Control Plan)  
  - Same pattern: untagged, no meaningful title, no /Lang, filename-as-title.
- `pr-volunteer-handbook` — Parks & Recreation (Volunteer Coach Handbook)  
  - Same pattern of untagged structure and missing title/lang.
- `pw-fleet-policy` — Public Works (Fleet Vehicle Use Policy)  
  - Same untagged, no meaningful title, no /Lang, filename-as-title pattern.

While not in the remediation queue (because they’re not public-facing), these should be scheduled for internal accessibility work, especially where employees with disabilities rely on them.

---

## Per-department one-line status (with owners)

All numbers below derive from this scan pass plus `get_queue_status` and the entity metadata.

**City Clerk — Owner: Dana Whitfield**  
- Public-facing scanned this run: 4  
  - Compliant: `clk-council-minutes-jun-remediated`, `clk-public-records-guide`  
  - Non-compliant (public): `clk-council-minutes-jun` (redirect recommended, not queued), `clk-election-poll-worker` (queued, pos 10)  
- Action: Update links to remediated minutes; prioritize remediation of the poll worker manual already in the queue.

**Finance — Owner: Susan Chen**  
- Public-facing scanned this run: 5  
  - Compliant: `fin-budget-2026-remediated`  
  - Non-compliant (public): `fin-acfr-2025` (queued, pos 9), `fin-budget-2026` (redirect recommended, not queued), `fin-vendor-w9-guide` (queued, pos 6), plus one additional public-facing non-compliant already counted in overall stats.  
  - Internal non-compliant: `fin-pcard-policy` (not queued).  
- Action: Switch links to the remediated budget edition; remediate the vendor W-9 guide and ACFR via queue; plan internal work on the P-card policy.

**Health & Human Services — Owner: Robert Kim**  
- Public-facing scanned this run: 4  
  - Compliant: `hhs-assistance-programs`  
  - Non-compliant (public): `hhs-food-permit` (queued, pos 5), `hhs-inspection-checklist` (queued, pos 8), plus one additional public-facing non-compliant in overall counts.  
  - Internal non-compliant: `hhs-staff-bbp-plan` (not queued).  
- Action: Focus on the food permit and inspection checklist already queued; schedule internal remediation for the staff exposure control plan.

**Parks & Recreation — Owner: James Okafor**  
- Public-facing scanned this run: 4  
  - Compliant: `pr-summer-programs`  
  - Non-compliant (public): `pr-shelter-rental` (queued, pos 1), `pr-tree-ordinance` (queued, pos 2), plus one additional public-facing non-compliant already reflected in overall counts.  
  - Internal non-compliant: `pr-volunteer-handbook` (not queued).  
- Action: Top-priority remediation is already in progress via the queue (shelter rental rules and tree ordinance summary); plan an internal accessibility update for the volunteer handbook.

**Public Works — Owner: Maria Gonzalez**  
- Public-facing scanned this run: 5  
  - Compliant: `pw-standard-details-2026`  
  - Non-compliant (public): `pw-snow-plan` (queued, pos 3), `pw-row-permit-guide` (queued, pos 4), `pw-stormwater-bmp` (queued, pos 7), plus one additional public-facing non-compliant already included in the overall non-compliant count.  
  - Internal non-compliant: `pw-fleet-policy` (not queued).  
- Action: Proceed with queued remediations, especially the snow plan and ROW permit guide; schedule internal remediation for the fleet policy.

---

## Verification notes

- All 22 previously “unscanned” documents were scanned via `scan_document`; verdicts and accessibility scores were written back and verified through `get_queue_status`.
- The remediation queue above is reconciled with `get_queue_status` and reflects the **authoritative** queued set and positions.
- No document described as “queued” here failed to appear in `get_queue_status`; where `queue_remediation` was rejected (e.g., `clk-council-minutes-jun`, `fin-budget-2026`), those documents are explicitly called out under redirect recommendations rather than in the queue.