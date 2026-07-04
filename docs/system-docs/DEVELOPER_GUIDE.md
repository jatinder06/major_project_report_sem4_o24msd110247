# Developer Guide

This guide describes the current `src/adk_agent` implementation for public-repo contributors and reviewers.

## 1. Architecture

The system has four main layers.

| Layer | Responsibility | Key modules |
| --- | --- | --- |
| Presentation | Streamlit dashboard and standalone demo | `dashboard.py`, `demo.py` |
| Agent orchestration | Google ADK root agent, specialist agents, callbacks, retry handling | `agent.py`, `callbacks.py`, `gemini_retry.py`, `persistent_runtime.py` |
| Model serving | FastAPI REST boundary for local model inference | `model_server.py`, `tools/model_client.py`, `tools/model_loader.py` |
| Evidence storage | SQLite monitoring/demo/cost rows and JSONL audit logs | `monitoring_store.py`, `audit.py`, `cost_tracking.py` |

The dashboard and ADK tools do not load heavy ML artefacts directly. They call the model server through `tools/model_client.py`.

## 2. Agent Graph

`src/adk_agent/agent.py` defines a Google ADK root agent and six specialist agent/tool families:

- sentiment
- churn
- segmentation
- support intent
- content strategy
- recommendation action

The churn family supports both structured XGBoost churn scoring and text-based Qwen LoRA churn classification through separate model-server endpoints.

## 3. Tool Interface Pattern

Tool wrappers live under `src/adk_agent/tools/`.

| Tool module | Purpose |
| --- | --- |
| `sentiment_tools.py` | Sentiment classification |
| `churn_tools.py` | Structured and text-based churn prediction |
| `segmentation_tools.py` | Customer segment classification |
| `support_tools.py` | Support intent classification |
| `content_tools.py` | Content strategy classification |
| `recommendation_tools.py` | Product recommendation action classification |
| `model_client.py` | Shared HTTP client for the model server |
| `model_loader.py` | Local artefact loading inside the model-server process |

Wrapper rule:

1. Validate/shape tool input.
2. Call `predict(endpoint, payload)`.
3. Return structured dictionaries suitable for ADK responses and dashboard traces.

## 4. Model Server

Start with:

```bash
python -m src.adk_agent.model_server
```

Default port: `8100`.

Primary endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Health check and loaded-model list |
| `POST /predict/sentiment` | Single sentiment prediction |
| `POST /predict/sentiment/batch` | Batch sentiment prediction |
| `POST /predict/churn_xgboost` | Structured churn probability |
| `POST /predict/churn_llm` | Text-based churn classification |
| `POST /predict/segmentation` | Customer segment classification |
| `POST /predict/segmentation/batch` | Batch segment classification |
| `POST /predict/support` | Support intent classification |
| `POST /predict/content` | Content strategy classification |
| `POST /predict/recommendation` | Recommendation action classification |
| `POST /predict/recommendation/batch` | Batch recommendation action classification |

The endpoint surface provides seven prediction capabilities, with selected batch routes and a health check.

## 5. Persistence

`monitoring_store.py` creates `data/adk_monitoring.db` with tables for:

- `monitoring_events`
- `demo_runs`
- `model_cost_events`

`persistent_runtime.py` uses ADK database sessions when `DatabaseSessionService` is available and falls back to in-memory sessions otherwise. The dashboard displays runtime status so the system does not overclaim persistence when the installed ADK environment lacks database-session support.

`audit.py` writes JSONL audit records to:

```text
logs/adk_audit.log
```

## 6. Cost Evidence

`cost_tracking.py` estimates Gemini-equivalent cost for locally served specialist model calls. This is evidence for API-cost avoidance on selected specialist calls, not a full infrastructure cost claim.

Pricing basis can be configured:

```bash
export GEMINI_COST_BASIS_MODEL="gemini-2.5-flash-lite"
export GEMINI_FLASH_LITE_INPUT_USD_PER_1M="0.10"
export GEMINI_FLASH_LITE_OUTPUT_USD_PER_1M="0.40"
```

## 7. Authentication and Roles

`auth.py` reads local dashboard users from `ADK_DASHBOARD_USERS`.

Format:

```bash
export ADK_DASHBOARD_USERS="admin:<change-me>:data_scientist,marketing:<change-me>:marketing_manager,viewer:<change-me>:viewer"
```

Valid roles:

- `admin`
- `data_scientist`
- `marketing_manager`
- `viewer`

Default credentials are local demo credentials only.

## 8. Retry and Quota Handling

`gemini_retry.py` patches Google GenAI/ADK model calls to handle 429 quota errors with retry, exponential backoff, and a configurable minimum interval.

Useful variables:

```bash
export GEMINI_RETRY_ATTEMPTS="5"
export GEMINI_RETRY_BACKOFF_FACTOR="2"
export GEMINI_MIN_CALL_INTERVAL_SECONDS="4"
```

The pacing is per process. Multiple running processes can still exceed external quota limits.

## 9. Testing

Run:

```bash
python -m unittest discover -s tests/adk_agent -p "test_*.py" -v
```

Current focus:

- auth parsing and login behaviour
- audit log write/read/clear
- SQLite monitoring persistence
- persistent runtime fallback
- Gemini retry and pacing
- tool wrapper HTTP behaviour
- FastAPI route design with fake model objects
- cost-evidence calculations

Tests avoid loading full transformer or XGBoost artefacts unless a specific integration environment is prepared.

## 10. Adding a New Specialist Tool

1. Add a wrapper in `src/adk_agent/tools/`.
2. Add or reuse a model-server endpoint in `model_server.py`.
3. Register the tool with the relevant specialist ADK agent in `agent.py`.
4. Add callback/audit context if the tool should appear in monitoring dashboards.
5. Add a focused unit test under `tests/adk_agent/`.
6. Update this documentation and the public README.

## 11. Public-Repo Boundaries

This repository does not claim:

- live outbound campaign dispatch
- production CRM writes
- enterprise SSO
- enterprise encryption/key management
- full MLOps or drift-triggered retraining
- multi-process Gemini quota coordination

Those are future enhancements, not current public-release capabilities.
