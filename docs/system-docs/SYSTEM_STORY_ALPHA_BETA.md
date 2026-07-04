# Alpha and Beta Customer-Experience Story

This document explains the two demonstration scenarios used by the ADK-based Digital Marketing Intelligence System.

The stories are simulated business workflows. They show how specialist model outputs, ADK tool calls, monitoring, audit evidence, and dashboard review can work together. They do not perform live outbound campaign dispatch or update external business systems.

## 1. Why the Stories Exist

The project is not only a collection of trained models. Its main value is showing how trained/evaluated marketing intelligence capabilities can be orchestrated and inspected inside one workflow.

The Alpha and Beta stories make that value visible:

- Alpha shows a product-company customer journey.
- Beta shows a service-company customer journey.
- Both stories persist outputs so reviewers can inspect results after navigation or reruns.

## 2. System Layers Used by Both Stories

| Layer | Role in the story |
| --- | --- |
| Streamlit | Presents run controls, outputs, metrics, logs, and architecture views |
| Google ADK | Coordinates root-agent and specialist-agent execution |
| FastAPI model server | Serves local specialist model predictions |
| Specialist models | DistilBERT, XGBoost, and Qwen LoRA adapters provide task evidence |
| SQLite | Stores monitoring events, demo runs, and model-cost evidence |
| JSONL audit log | Records user-scoped actions |

## 3. Alpha: Product-Company Scenario

Alpha represents an ecommerce/product business that needs better targeting, review understanding, and recommendation actions.

### Before the System

Alpha's marketing workflow is fragmented:

- customer segments are reviewed manually
- review sentiment is checked late
- recommendation evidence is disconnected from campaign decisions
- technical evidence disappears after a one-off script run

### Demonstrated Workflow

The Alpha story combines:

1. customer segmentation evidence
2. churn/sentiment monitoring evidence
3. recommendation action classification
4. persisted monitoring and cost evidence

### Customer-Experience Value

Alpha demonstrates how a product business can move from broad, generic actions to more targeted customer-experience decisions:

- identify useful customer groups
- spot sentiment/risk patterns
- classify review-driven recommendation action
- review the evidence behind each decision

The system does not send real emails, publish real social posts, or write to a live ecommerce platform.

## 4. Beta: Service-Company Scenario

Beta represents a subscription/service business where retention and support quality are central to customer experience.

### Before the System

Beta's workflow is also fragmented:

- churn risk is reviewed separately from support signals
- support tickets are manually triaged
- negative sentiment may be discovered after customers have already escalated
- evidence is spread across tools and cannot easily be audited

### Demonstrated Workflow

The Beta story combines:

1. structured churn scoring
2. text-based churn classification
3. support intent routing
4. crisis sentiment monitoring
5. persisted monitoring and cost evidence

### Customer-Experience Value

Beta demonstrates how a service business can inspect retention and service-quality signals together:

- identify churn-risk patterns
- route support messages by intent
- detect sentiment risk
- retain traceable evidence for review

The system does not contact customers, update a ticketing platform, or trigger live retention offers.

## 5. What Reviewers Should Inspect

After running Alpha or Beta, reviewers should inspect:

- demo output tables
- model/tool event counts
- latency and token metrics
- Gemini-equivalent cost evidence
- monitoring-event rows
- audit-log entries
- persisted `demo_runs` summaries

The key point is persistence. Results should remain visible after switching pages because the system writes demo outputs and monitoring evidence to local storage.

## 6. Suggested Demonstration Path

1. Start the model server:

   ```bash
   python -m src.adk_agent.model_server
   ```

2. Start the dashboard:

   ```bash
   streamlit run src/adk_agent/dashboard.py
   ```

3. Login as Data Scientist or Marketing Manager.

4. Open `Demo Simulation`.

5. Run `Alpha Story`.

6. Run `Beta Story`.

7. Open:

   - `Demo Performance Dashboard`
   - `Demo Before vs After Impact`
   - `Demo Log Explorer`
   - `Demo System Architecture`

8. Switch pages and confirm that output remains available.

## 7. Academic Framing

The stories should be described as simulated customer-experience workflows. They support the MSc project by demonstrating:

- multi-agent orchestration
- local specialist model serving
- role-aware dashboard access
- persistent monitoring
- audit logging
- reproducible evidence
- cost-awareness for local specialist calls

They should not be described as production marketing automation or live campaign execution.
