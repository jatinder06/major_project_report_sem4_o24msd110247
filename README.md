# AI-Driven Tools in Digital Marketing: Enhancing Customer Experience


This repository contains the source code for the MSc Data Science major project **AI-Driven Tools in Digital Marketing: Enhancing Customer Experience**. The project addresses fragmented marketing AI tooling, proprietary LLM cost and quota pressure, limited task specialisation, weak workflow coordination, and insufficient audit governance by implementing a cost-aware agentic AI platform for customer-experience workflows. It combines Google ADK orchestration, six specialist sub-agents, FastAPI-served model artefacts, ADK tool wrappers, Streamlit role-based monitoring, SQLite/JSONL persistence, and automated `unittest` verification. The implemented system unifies sentiment analysis, churn prediction, customer segmentation, support intent routing, content strategy, and product recommendation in one auditable workflow, achieving 79.85% held-out accuracy and 0.9319 ROC-AUC for DistilBERT sentiment classification, 0.8460 ROC-AUC for Optuna-tuned XGBoost churn prediction, and 74.0% to 98.2% accuracy across five Qwen 2.5 0.5B LoRA-adapted marketing tasks.


The system is designed around six specialist agents:


- Sentiment analysis for customer reviews and feedback.
- Churn prediction with structured XGBoost and text-based LLM models.
- Customer segmentation for marketing groups.
- Support intent classification.
- Content strategy recommendation.
- Product recommendation decisioning from review text.


## Repository Layout


```text
.
├── configs/
│   └── config.yaml                  # Runtime model configuration used by src/adk_agent/agent.py
├── experimentation/
│   └── notebooks/                   # Training, fine-tuning, and evaluation notebooks
├── src/adk_agent/
│   ├── agent.py                     # Google ADK orchestrator and specialist agents
│   ├── model_server.py              # FastAPI inference server for local models
│   ├── dashboard.py                 # Main Streamlit dashboard
│   ├── demo.py                      # Streamlit demo/simulation pages
│   ├── tools/                       # Agent tool wrappers and model-loading utilities
│   └── eval/                        # ADK evaluation cases
├── tests/adk_agent/                 # Unit tests for current ADK code
├── quick_test.sh                    # Lightweight smoke test
├── requirements.txt                 # Notebook/training dependencies
└── LICENSE

```


## What Is Included


- Google ADK root orchestrator with six specialist sub-agents.
- ADK tool wrappers that call a separate FastAPI model server.
- Fine-tuned DistilBERT sentiment classification, Qwen 2.5 LoRA-style specialist adapters, and Optuna-tuned XGBoost churn modelling evidence.
- Streamlit dashboard pages for role-aware login, system overview, model/tool performance, log exploration, user audit, live agent testing, and Alpha/Beta customer-journey demonstrations.
- SQLite-backed monitoring, demo-result, model-cost, and ADK session evidence where available, plus JSONL audit logging.
- Gemini retry/pacing, token monitoring, and cost-evidence calculation.
- unittest-based tests for auth, persistence, monitoring, tools, retry behavior, cost tracking, and model-server APIs.


## Public Release Notes


Large generated artifacts and private local data should not be committed to the public repository. The code expects trained model artifacts under `experimentation/artifacts/` and a converted local base model under `models/` for full local inference, but those files are usually too large for Git. Public users can restore the required runtime artifacts from this Google Drive folder: [project model artifacts](https://drive.google.com/drive/folders/1SEJMGkx_BRlGdf98nxIfd_P8fBERflYe?usp=sharing).


Before publishing, make sure no real secrets are committed. In particular, replace or remove any local `.env` files and configure credentials through environment variables.


## Requirements


Use a conda environment with Python 3.11+ for the application stack.


The checked-in `requirements.txt` covers notebook and training dependencies. To run the ADK app and dashboards, install the runtime packages as well:


```bash
# Create and activate a conda environment
conda create -n adk-marketing python=3.11 pip
conda activate adk-marketing
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install fastapi "uvicorn[standard]" streamlit httpx pydantic python-dotenv plotly gdown
python -m pip install google-adk google-genai

```


For optional LiteLLM/OpenRouter support:


```bash
python -m pip install litellm

```


The full stack also requires:


- Runtime model artifacts from the consolidated Google Drive folder.
- A working Gemini API key with access to the root-agent model configured in configs/config.yaml, currently gemini-2.5-flash-lite.
- Network access for dependency installation, artifact download, and the Gemini validation request.


## Configuration


The active source configuration is [configs/config.yaml](configs/config.yaml). The ADK app reads the `adk_agent` section for Gemini/LiteLLM model names. By default, the root marketing orchestrator uses Gemini through `orchestrator_model_gemini`; specialist sub-agents use `sub_agent_model_gemini`.


Common environment variables:


```bash
export GOOGLE_API_KEY="your_google_or_gemini_api_key"
# or
export GEMINI_API_KEY="your_google_or_gemini_api_key"

export MODEL_SERVER_URL="http://localhost:8100"
export ADK_SESSION_DB_URL="sqlite:///data/adk_sessions.db"
export ADK_LOG_LEVEL="INFO"

```


The stack launcher validates `GOOGLE_API_KEY` or `GEMINI_API_KEY` by making a small Gemini request against the configured root-agent model before starting the dashboard. If the key is missing, expired, quota-limited, or not allowed to access the configured model, startup stops with a validation error. For LiteLLM/OpenRouter experiments, set `USE_LITELLM=true`; for local smoke testing only, set `SKIP_GEMINI_CHECK=1`.


Dashboard users can be configured with:


```bash
export ADK_DASHBOARD_USERS="admin:admin123:data_scientist,marketing:mkt2024:marketing_manager,viewer:view123:viewer"

```


If `ADK_DASHBOARD_USERS` is not set, the dashboard falls back to local demo users.


## Quick Smoke Test


Run the lightweight repository smoke test:


```bash
./quick_test.sh

```


The script resolves the project root from its own location, expects an active conda environment, installs missing quick-test dependencies into that environment, and skips model inference if the local model server is not running.


## Running The System


### Start The Complete Stack


The recommended public entry point is:


```bash
export GOOGLE_API_KEY="your_google_or_gemini_api_key"
./start_stack.sh

```


`start_stack.sh` expects an active conda environment, validates `requirements.txt` on every run, installs dependencies into that environment, downloads missing model artifacts from [the consolidated project Drive folder](https://drive.google.com/drive/folders/1SEJMGkx_BRlGdf98nxIfd_P8fBERflYe?usp=sharing), validates Gemini root-agent access, runs unit tests, starts the FastAPI model server, waits for `/health`, and opens the Streamlit dashboard process.


Useful overrides:


```bash
FORCE_INSTALL=1 ./start_stack.sh
FORCE_ARTIFACT_DOWNLOAD=1 ./start_stack.sh
SKIP_ARTIFACT_DOWNLOAD=1 ./start_stack.sh
SKIP_GEMINI_CHECK=1 ./start_stack.sh
SKIP_TESTS=1 ./start_stack.sh
STREAMLIT_PORT=8502 ./start_stack.sh

```


### 1. Start The Model Server


The model server loads local model artifacts and exposes prediction endpoints on port `8100`.


```bash
python -m src.adk_agent.model_server

```


Health check:


```bash
curl http://localhost:8100/health

```


### 2. Run The Streamlit Dashboard


In a second terminal:


```bash
streamlit run src/adk_agent/dashboard.py

```


The authenticated dashboard is the recommended formal demonstration surface. A typical flow is to log in, check the ADK session status indicator, run the Alpha Story and Beta Story, inspect the performance/dashboard evidence, then open Log Explorer and User Audit to confirm persisted runtime records.


### 3. Run The Standalone Demo Dashboard


```bash
streamlit run src/adk_agent/demo.py

```


### 4. Run ADK From The Command Line


Interactive ADK surfaces:


```bash
adk web src.adk_agent
adk run src.adk_agent

```


Single command-line query:


```bash
python -m src.adk_agent.run "Analyze the sentiment of: Great product!"

```


With telemetry:


```bash
python -m src.adk_agent.run --telemetry "Is this customer at risk? tenure=3, contract=Month-to-month"

```


## Model Artifacts


Full local inference requires generated artifacts from the notebooks. The stack launcher downloads missing artifacts from [the consolidated project Google Drive folder](https://drive.google.com/drive/folders/1SEJMGkx_BRlGdf98nxIfd_P8fBERflYe?usp=sharing). That folder should include both `experimentation/artifacts/` and the converted `models/` directory inside the same top-level `artifacts` export. Expected artifact locations include:


- experimentation/artifacts/distilbert_sentiment_production/final_model/
- experimentation/artifacts/churn_xgboost_production/model/
- experimentation/artifacts/churn_llm_production/
- experimentation/artifacts/segmentation_llm_v2_robust/
- experimentation/artifacts/support_llm_production/
- experimentation/artifacts/content_llm_production/
- experimentation/artifacts/recommendation_llm_production/
- models/qwen2.5-0.5b-instruct-hf/


If these artifacts are missing, source imports and tests can still run, but the model server cannot perform real local inference until the artifacts are created or restored.


## Experiments


The experiment notebooks live in `experimentation/notebooks/`:


- 01_distilbert_sentiment_production_finetuning.ipynb
- 02_segmentation_agent_production_finetuning.ipynb
- 03_recommendation_agent_production_finetuning.ipynb
- 03_segmentation_llm_v2_robust_finetuning.ipynb
- 04_churn_agent_phi3_finetuning.ipynb
- 05_content_agent_mistral_finetuning.ipynb
- 06_support_agent_llama_finetuning.ipynb
- 07_churn_xgboost_vs_llm.ipynb


Start Jupyter with:


```bash
jupyter notebook experimentation/notebooks

```


## Testing


Run the current unit tests with:


```bash
python -m unittest discover -s tests/adk_agent

```


Compile the ADK code paths:


```bash
python -m py_compile src/adk_agent/*.py src/adk_agent/tools/*.py src/adk_agent/eval/*.py

```


The tests are written with Python's standard-library `unittest` framework. Some tests use fakes/mocks and do not require large model artifacts.


## API Endpoints


When `src.adk_agent.model_server` is running, it exposes:


- GET /health
- POST /predict/sentiment
- POST /predict/sentiment/batch
- POST /predict/churn_xgboost
- POST /predict/churn_llm
- POST /predict/segmentation
- POST /predict/segmentation/batch
- POST /predict/support
- POST /predict/content
- POST /predict/recommendation
- POST /predict/recommendation/batch


Example:


```bash
curl -X POST http://localhost:8100/predict/sentiment \
  -H "Content-Type: application/json" \
  -d '{"text":"This product exceeded my expectations."}'

```


## Notes For Contributors


- Keep secrets out of Git. Use environment variables or local .env files ignored by Git.
- Do not commit large model artifacts, datasets, caches, logs, or notebook output bloat.
- Prefer current src/adk_agent modules. Older root-level demo scripts from previous framework versions should not be reintroduced.
- Keep tests focused on current ADK behavior and mock large model dependencies where possible.


## License


This project is released under the MIT License. See [LICENSE](LICENSE).


