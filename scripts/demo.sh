#!/usr/bin/env bash
# One-command demo for AccessCatalog Agent.
#
# Prereqs (see README):
#   - DataHub running locally:  datahub docker quickstart
#   - .env with OPENAI_API_KEY (copy .env.example)
#   - deps installed:           uv pip install -e . mcp-server-datahub
#
# What it does:
#   1. Registers the 22-document corpus in DataHub (unscanned baseline)
#   2. Runs the agent: real PDF scans -> write-back -> lineage-aware queue
#   3. Generates compliance reports from live catalog state

set -euo pipefail
cd "$(dirname "$0")/.."

if ! curl -sf http://localhost:8080/health >/dev/null 2>&1; then
    echo "DataHub GMS is not reachable at localhost:8080."
    echo "Start it with: datahub docker quickstart"
    exit 1
fi
if [ ! -f .env ] && [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "No OPENAI_API_KEY found. Copy .env.example to .env and add your key."
    exit 1
fi

echo "==> [1/3] Registering document corpus in DataHub (unscanned baseline)"
accesscatalog ingest

echo
echo "==> [2/3] Running the compliance agent (takes a few minutes)"
echo "    Watch live in the DataHub UI (http://localhost:9002, datahub/datahub):"
echo "    search 'tags:unscanned' and refresh as verdicts are written back."
accesscatalog agent

echo
echo "==> [3/3] Generating compliance reports from live catalog state"
accesscatalog report
accesscatalog status

echo
echo "Done. Open reports/compliance_report.html and reports/agent_summary.md"
