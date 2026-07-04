#!/usr/bin/env bash

# Quick smoke tests for the current ADK agent code.
# The script resolves the project root from its own location and expects an
# active conda environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$SCRIPT_DIR}"

cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

if [[ ! -f "$PROJECT_ROOT/requirements.txt" ]]; then
    echo "ERROR: requirements.txt not found in $PROJECT_ROOT" >&2
    exit 1
fi

if [[ -n "${PYTHON:-}" ]]; then
    PY="$PYTHON"
elif [[ -n "${CONDA_PREFIX:-}" && -x "$CONDA_PREFIX/bin/python" ]]; then
    PY="$CONDA_PREFIX/bin/python"
else
    echo "ERROR: Activate a conda environment with Python 3.11+ before running quick_test.sh, or set PYTHON=/path/to/python." >&2
    exit 1
fi

check_python_version() {
    "$PY" - <<'PY'
import sys

if sys.version_info < (3, 11):
    raise SystemExit(f"Python 3.11+ required, found {sys.version.split()[0]}")
PY
}

check_python_version

deps_ready() {
    "$PY" - <<'PY' >/dev/null 2>&1
import httpx
import yaml
PY
}

if [[ "${FORCE_INSTALL:-0}" == "1" ]] || ! deps_ready; then
    echo "Installing project dependencies into the active environment"
    "$PY" -m pip install --upgrade pip
    "$PY" -m pip install -r "$PROJECT_ROOT/requirements.txt"
    "$PY" -m pip install httpx pydantic python-dotenv
fi

if ! deps_ready; then
    echo "ERROR: Required quick-test dependencies are still missing after install." >&2
    echo "Try: FORCE_INSTALL=1 ./quick_test.sh" >&2
    exit 1
fi

if command -v realpath >/dev/null 2>&1; then
    PY_DISPLAY="$(realpath "$PY")"
else
    PY_DISPLAY="$PY"
fi

echo "======================================================================"
echo "  ADK Agent - Quick Smoke Test"
echo "======================================================================"
echo "Project root: $PROJECT_ROOT"
if [[ -n "${CONDA_DEFAULT_ENV:-}" ]]; then
    echo "Conda env: ${CONDA_DEFAULT_ENV}"
fi
echo "Python: $PY_DISPLAY"
echo ""

run_python() {
    "$PY" - "$@"
}

echo "----------------------------------------------------------------------"
echo "1. Validate project layout"
echo "----------------------------------------------------------------------"
run_python <<'PY'
from pathlib import Path

root = Path.cwd()
required = [
    root / "configs" / "config.yaml",
    root / "src" / "adk_agent" / "agent.py",
    root / "src" / "adk_agent" / "model_server.py",
    root / "src" / "adk_agent" / "tools" / "sentiment_tools.py",
]
missing = [str(path) for path in required if not path.exists()]
if missing:
    raise SystemExit("Missing required files:\n" + "\n".join(missing))
print("OK: required project files exist")
PY

echo ""
echo "----------------------------------------------------------------------"
echo "2. Validate YAML config"
echo "----------------------------------------------------------------------"
run_python <<'PY'
from pathlib import Path
import yaml

config = yaml.safe_load((Path.cwd() / "configs" / "config.yaml").read_text()) or {}
adk = config.get("adk_agent", {})
required = [
    "default_model_gemini",
    "sub_agent_model_gemini",
    "orchestrator_model_gemini",
    "orchestrator_model_litellm",
]
missing = [key for key in required if not adk.get(key)]
if missing:
    raise SystemExit(f"Missing adk_agent config keys: {missing}")
print("OK: config.yaml contains current ADK model settings")
PY

echo ""
echo "----------------------------------------------------------------------"
echo "3. Import current source modules"
echo "----------------------------------------------------------------------"
run_python <<'PY'
import importlib

modules = [
    "src.adk_agent.tools.model_client",
    "src.adk_agent.tools.sentiment_tools",
    "src.adk_agent.tools.churn_tools",
    "src.adk_agent.tools.segmentation_tools",
    "src.adk_agent.tools.support_tools",
    "src.adk_agent.tools.content_tools",
    "src.adk_agent.tools.recommendation_tools",
    "src.adk_agent.persistent_runtime",
    "src.adk_agent.monitoring_store",
]
for name in modules:
    importlib.import_module(name)

if importlib.util.find_spec("google.adk") is None:
    print("SKIP: src.adk_agent.agent import requires google.adk")
else:
    importlib.import_module("src.adk_agent.agent")
    print("OK: src.adk_agent.agent imports successfully")

print("OK: current lightweight src.adk_agent modules import successfully")
PY

echo ""
echo "----------------------------------------------------------------------"
echo "4. Check stale legacy package paths are absent"
echo "----------------------------------------------------------------------"
run_python <<'PY'
from pathlib import Path

root = Path.cwd()
legacy_paths = [
    root / "src" / "agents",
    root / "src" / "memory",
    root / "src" / "session",
]
present = [str(path) for path in legacy_paths if path.exists()]
if present:
    raise SystemExit("Legacy package paths still present:\n" + "\n".join(present))
print("OK: legacy src.agents/src.memory/src.session package paths are absent")
PY

echo ""
echo "----------------------------------------------------------------------"
echo "5. Check model server health"
echo "----------------------------------------------------------------------"
run_python <<'PY'
from src.adk_agent.tools.model_client import server_healthy

if server_healthy():
    print("OK: model server is healthy")
else:
    print("SKIP: model server is not running; start it with python -m src.adk_agent.model_server")
PY

echo ""
echo "----------------------------------------------------------------------"
echo "6. Optional sentiment inference smoke test"
echo "----------------------------------------------------------------------"
run_python <<'PY'
from src.adk_agent.tools.model_client import server_healthy
from src.adk_agent.tools.sentiment_tools import analyze_sentiment

if not server_healthy():
    print("SKIP: sentiment inference requires the model server")
else:
    result = analyze_sentiment("This product exceeded my expectations.")
    if result.get("status") != "success":
        raise SystemExit(f"Sentiment inference failed: {result}")
    print(f"OK: sentiment={result['label']} confidence={result['confidence']}")
PY

echo ""
echo "======================================================================"
echo "  Quick smoke test complete"
echo "======================================================================"
