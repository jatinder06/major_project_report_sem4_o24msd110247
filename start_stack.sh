#!/usr/bin/env bash

# Install dependencies when needed, run unit tests, then start the local stack:
#   1. FastAPI model server on port 8100
#   2. Streamlit dashboard on port 8501
#
# Usage:
#   ./start_stack.sh
#
# Useful overrides:
#   PYTHON=/path/to/python ./start_stack.sh
#   PROJECT_ROOT=/path/to/repo ./start_stack.sh
#   FORCE_INSTALL=1 ./start_stack.sh
#   FORCE_ARTIFACT_DOWNLOAD=1 ./start_stack.sh
#   SKIP_ARTIFACT_DOWNLOAD=1 ./start_stack.sh
#   SKIP_GEMINI_CHECK=1 ./start_stack.sh
#   SKIP_TESTS=1 ./start_stack.sh
#   STREAMLIT_PORT=8502 ./start_stack.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$SCRIPT_DIR}"
STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"
MODEL_SERVER_URL="${MODEL_SERVER_URL:-http://localhost:8100}"
ARTIFACTS_DRIVE_URL="${ARTIFACTS_DRIVE_URL:-https://drive.google.com/drive/folders/1SEJMGkx_BRlGdf98nxIfd_P8fBERflYe?usp=sharing}"

cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export MODEL_SERVER_URL

python_site_packages() {
    "$PY" - <<'PY'
import sysconfig

print(sysconfig.get_paths()["purelib"])
PY
}

choose_pip_helper_python() {
    local candidate

    for candidate in python python3 python3.13 python3.12; do
        if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -m pip --version >/dev/null 2>&1; then
            command -v "$candidate"
            return 0
        fi
    done

    return 1
}

bootstrap_pip_from_helper() {
    local helper_python helper_site_packages

    helper_python="$(choose_pip_helper_python)" || return 1
    helper_site_packages="$(python_site_packages)"

    echo "Seeding pip into the active Python environment using $helper_python..."
    "$helper_python" -m pip install --upgrade --target "$helper_site_packages" pip setuptools wheel
}

choose_runtime_python() {
    if [[ -n "${PYTHON:-}" ]]; then
        printf '%s\n' "$PYTHON"
    elif [[ -n "${CONDA_PREFIX:-}" && -x "$CONDA_PREFIX/bin/python" ]]; then
        printf '%s\n' "$CONDA_PREFIX/bin/python"
    elif command -v python >/dev/null 2>&1; then
        command -v python
    else
        echo "ERROR: Activate a conda environment with Python 3.11+ first, or set PYTHON=/path/to/python." >&2
        exit 1
    fi
}

PY="$(choose_runtime_python)"
PIP="$PY -m pip"

check_python_version() {
    "$PY" - <<'PY'
import sys

if sys.version_info < (3, 11):
    raise SystemExit(f"Python 3.11+ required, found {sys.version.split()[0]}")
PY
}

check_python_version

ensure_pip() {
    if "$PY" -m pip --version >/dev/null 2>&1; then
        return 0
    fi

    echo "Python environment is missing pip; bootstrapping it with ensurepip..."
    if "$PY" -m ensurepip --upgrade >/dev/null 2>&1; then
        return 0
    fi

    if bootstrap_pip_from_helper; then
        return 0
    fi

    cat >&2 <<'EOF'
ERROR: Could not bootstrap pip inside the active Python environment.
Activate a conda environment with pip installed, or point PYTHON at a healthy interpreter.
EOF
    exit 1
}

echo "======================================================================"
echo "  AI Marketing ADK Stack Launcher"
echo "======================================================================"
echo "Project root: $PROJECT_ROOT"
echo "Python: $($PY --version 2>&1) ($PY)"
if [[ -n "${CONDA_DEFAULT_ENV:-}" ]]; then
    echo "Conda env: ${CONDA_DEFAULT_ENV}"
fi
echo "Model server: $MODEL_SERVER_URL"
echo "Streamlit: http://localhost:$STREAMLIT_PORT"
echo "Artifacts: $ARTIFACTS_DRIVE_URL"
echo ""

echo "Validating requirements.txt and runtime dependencies..."
ensure_pip
$PIP install --upgrade pip
$PIP install -r requirements.txt
$PIP install fastapi "uvicorn[standard]" streamlit httpx pydantic python-dotenv plotly google-adk google-genai gdown

if [[ "${FORCE_INSTALL:-0}" == "1" ]]; then
    echo "FORCE_INSTALL=1 set; requirements and runtime dependencies were refreshed."
else
    echo "requirements.txt validated against the active conda environment."
fi

deps_ready() {
    ensure_pip
    "$PY" - <<'PY' >/dev/null 2>&1
import gdown
import google.genai
import httpx
import streamlit
import uvicorn
import yaml
PY
}

if ! deps_ready; then
    echo "Active Python environment is missing stack dependencies. Installing missing runtime packages..."
    ensure_pip
    $PIP install -r requirements.txt
    $PIP install fastapi "uvicorn[standard]" streamlit httpx pydantic python-dotenv plotly google-adk google-genai gdown
fi

if ! deps_ready; then
    echo "ERROR: Required stack dependencies are still missing after installation." >&2
    echo "Try: FORCE_INSTALL=1 ./start_stack.sh" >&2
    exit 1
fi

artifacts_ready() {
    [[ -d "$PROJECT_ROOT/experimentation/artifacts/distilbert_sentiment_production/final_model" ]] &&
    [[ -d "$PROJECT_ROOT/experimentation/artifacts/churn_xgboost_production/model" ]] &&
    [[ -d "$PROJECT_ROOT/experimentation/artifacts/churn_llm_production" ]] &&
    [[ -d "$PROJECT_ROOT/experimentation/artifacts/segmentation_llm_v2_robust" ]] &&
    [[ -d "$PROJECT_ROOT/experimentation/artifacts/support_llm_production" ]] &&
    [[ -d "$PROJECT_ROOT/experimentation/artifacts/content_llm_production" ]] &&
    [[ -d "$PROJECT_ROOT/experimentation/artifacts/recommendation_llm_production" ]] &&
    [[ -d "$PROJECT_ROOT/models/qwen2.5-0.5b-instruct-hf" ]]
}

if [[ "${SKIP_ARTIFACT_DOWNLOAD:-0}" != "1" ]]; then
    if [[ "${FORCE_ARTIFACT_DOWNLOAD:-0}" == "1" ]] || ! artifacts_ready; then
        echo ""
        echo "Downloading model artifacts from Google Drive..."
        "$PY" -m gdown --folder "$ARTIFACTS_DRIVE_URL" -O "$PROJECT_ROOT" --remaining-ok
    else
        echo "Model artifacts already present. Set FORCE_ARTIFACT_DOWNLOAD=1 to download again."
    fi

    if ! artifacts_ready; then
        echo "ERROR: Required model artifacts are still missing after the Google Drive download." >&2
        echo "Confirm the Drive folder contains the consolidated experimentation/artifacts/... and models/qwen2.5-0.5b-instruct-hf/ contents." >&2
        echo "Drive folder: $ARTIFACTS_DRIVE_URL" >&2
        exit 1
    fi
else
    echo "Skipping artifact download because SKIP_ARTIFACT_DOWNLOAD=1"
fi

validate_gemini_access() {
    "$PY" - <<'PY'
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from google import genai

project_root = Path.cwd()
dotenv_path = project_root / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path, override=False)

if os.getenv("USE_LITELLM", "false").lower() == "true":
    print("Skipping Gemini validation because USE_LITELLM=true")
    raise SystemExit(0)

config = yaml.safe_load((project_root / "configs" / "config.yaml").read_text()) or {}
adk_config = config.get("adk_agent", {})
model = os.getenv(
    "ORCHESTRATOR_MODEL_GEMINI",
    adk_config.get("orchestrator_model_gemini")
    or adk_config.get("default_model_gemini")
    or "gemini-2.5-flash-lite",
)
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    raise SystemExit(
        "Missing Gemini API key. Set GOOGLE_API_KEY or GEMINI_API_KEY before starting the stack."
    )

client = genai.Client(api_key=api_key)
try:
    response = client.models.generate_content(
        model=model,
        contents="Reply with OK to validate access.",
    )
except Exception as exc:
    raise SystemExit(f"Gemini validation failed for model {model!r}: {exc}") from exc

text = getattr(response, "text", "") or ""
if not text.strip():
    raise SystemExit(f"Gemini validation failed for model {model!r}: empty response")

print(f"Gemini validation passed for root agent model: {model}")
PY
}

if [[ "${SKIP_GEMINI_CHECK:-0}" != "1" ]]; then
    echo ""
    echo "Validating Gemini API key and root agent model access..."
    validate_gemini_access
else
    echo "Skipping Gemini validation because SKIP_GEMINI_CHECK=1"
fi

if [[ "${SKIP_TESTS:-0}" != "1" ]]; then
    echo ""
    echo "Running unit tests..."
    "$PY" -m unittest discover -s tests/adk_agent
else
    echo "Skipping unit tests because SKIP_TESTS=1"
fi

MODEL_PID=""

cleanup() {
    if [[ -n "$MODEL_PID" ]] && kill -0 "$MODEL_PID" >/dev/null 2>&1; then
        echo ""
        echo "Stopping model server (PID $MODEL_PID)..."
        kill "$MODEL_PID" >/dev/null 2>&1 || true
        wait "$MODEL_PID" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT INT TERM

wait_for_model_server() {
    "$PY" - "$MODEL_SERVER_URL" <<'PY'
import sys
import time

import httpx

url = sys.argv[1].rstrip("/")
deadline = time.time() + 300
last_error = None

while time.time() < deadline:
    try:
        response = httpx.get(f"{url}/health", timeout=5.0)
        if response.status_code == 200:
            print(f"Model server is healthy: {url}/health")
            raise SystemExit(0)
        last_error = f"HTTP {response.status_code}"
    except Exception as exc:
        last_error = str(exc)
    time.sleep(3)

raise SystemExit(f"Model server did not become healthy within 300s: {last_error}")
PY
}

echo ""
echo "Starting model server..."
"$PY" -m src.adk_agent.model_server &
MODEL_PID="$!"

echo "Waiting for model server health check..."
wait_for_model_server

echo ""
echo "Starting Streamlit dashboard..."
echo "Open: http://localhost:$STREAMLIT_PORT"
"$PY" -m streamlit run src/adk_agent/dashboard.py --server.port "$STREAMLIT_PORT"
