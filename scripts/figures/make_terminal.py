"""Build the terminal figure from REAL `accesscatalog scan` output.

Nothing here is mocked up: the script shells out to the CLI, captures whatever
it prints, and wraps that verbatim text in a terminal frame. The only thing
added is the colour Rich would have applied on a real tty (it strips colour
when stdout is a pipe).
"""

from __future__ import annotations

import html
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PDFS = [
    ("corpus/pdfs/pw-snow-plan.pdf", "an untreated scan of the city's snow plan"),
    ("corpus/pdfs/pw-standard-details-2026.pdf", "a genuinely tagged PDF/UA file"),
]


def run_scan(rel_pdf: str) -> str:
    env = {**os.environ, "COLUMNS": "100", "TERM": "dumb"}
    proc = subprocess.run(
        [sys.executable, "-m", "accesscatalog.cli", "scan", rel_pdf],
        cwd=REPO, env=env, capture_output=True, text=True, check=True,
    )
    return proc.stdout.rstrip("\n")


def colourise(text: str) -> str:
    out = html.escape(text)
    out = out.replace("│ pass ", '│ <span class="ok">pass</span> ')
    out = out.replace("│ FAIL ", '│ <span class="no">FAIL</span> ')
    out = out.replace("│ critical ", '│ <span class="crit">critical</span> ')
    out = out.replace("│ warning  ", '│ <span class="warn">warning</span>  ')
    out = re.sub(r"Verdict: NON-COMPLIANT",
                 'Verdict: <span class="no b">NON-COMPLIANT</span>', out)
    out = re.sub(r"Verdict: COMPLIANT",
                 'Verdict: <span class="ok b">COMPLIANT</span>', out)
    # Rich centres the table title above the box; make it stand out like a title.
    out = re.sub(r"^(\s+)(\S.*score \d+/100)(\s*)$",
                 r'\1<span class="title">\2</span>\3', out, flags=re.M)
    return out


def main() -> None:
    blocks = []
    for rel_pdf, _note in PDFS:
        blocks.append(
            f'<span class="prompt">$</span> <span class="cmd">accesscatalog scan {rel_pdf}</span>\n'
            + colourise(run_scan(rel_pdf))
        )
    body = "\n\n".join(blocks)

    out = Path(__file__).with_name("terminal.html")
    out.write_text(TEMPLATE.replace("__BODY__", body), encoding="utf-8")
    print(f"wrote {out}")


TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<link rel="stylesheet" href="_base.css">
<style>
  body { width: 940px; overflow: hidden; }
  .frame { padding: 34px 40px 38px; }
  .eyebrow { margin-bottom: 14px; }
  .term { background: #06152b; border: 1px solid rgba(159,192,238,.22);
          border-radius: 13px; overflow: hidden; }
  .bar { display: flex; align-items: center; gap: 8px; padding: 11px 15px;
         background: rgba(20,51,95,.85); border-bottom: 1px solid rgba(159,192,238,.16); }
  .dot { width: 11px; height: 11px; border-radius: 50%; }
  .r { background: #ff5f57; } .y { background: #febc2e; } .g { background: #28c840; }
  .bar .t { margin-left: 8px; font-size: 12.5px; color: var(--muted);
            font-family: 'SF Mono', ui-monospace, Menlo, monospace; }
  pre { margin: 0; padding: 18px 20px 20px; white-space: pre;
        font-family: 'SF Mono', ui-monospace, Menlo, Consolas, monospace;
        font-size: 13px; line-height: 1.42; color: #cfe1ff; }
  .prompt { color: var(--green); font-weight: 700; }
  .cmd    { color: #fff; font-weight: 700; }
  .title  { color: var(--gold); font-weight: 700; }
  .ok   { color: #4fd166; } .no { color: #ff6b60; }
  .b    { font-weight: 700; }
  .crit { color: #ffb0a8; } .warn { color: var(--gold); }
  .note { margin-top: 15px; font-size: 14px; color: var(--text); }
  .note b { color: var(--gold); }
</style></head>
<body><div class="frame">
  <div class="eyebrow">Real scans, not mocks</div>
  <div class="term">
    <div class="bar"><i class="dot r"></i><i class="dot y"></i><i class="dot g"></i>
      <span class="t">accesscatalog — Section 508 / WCAG checks on real PDF internals</span></div>
    <pre>__BODY__</pre>
  </div>
  <p class="note">The scanner reads the actual PDF: <b>structure tree</b> (<span class="mono">StructTreeRoot</span>/<span class="mono">MarkInfo</span>),
  document title, <span class="mono">/Lang</span>, image-only pages, form-field labels and bookmarks — each mapped to a
  Section 508 / WCAG criterion. Same corpus, same commands, on any machine.</p>
</div></body></html>
"""

if __name__ == "__main__":
    main()
