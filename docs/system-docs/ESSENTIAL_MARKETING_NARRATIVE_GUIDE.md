# Essential Marketing Narrative Guide

This guide helps explain the project in clear business language without overstating the implementation.

## 1. One-Line Positioning

The project is a Digital Marketing Intelligence System that uses ADK agents and fine-tuned open-source small-language-model artefacts to support customer-experience decisions in segmentation, churn, sentiment, support, content strategy, and recommendation workflows.

## 2. Short Elevator Pitch

Marketing teams often use separate tools for customer segmentation, sentiment analysis, churn prediction, support triage, content planning, and recommendation decisions. This project shows how those tasks can be coordinated through an ADK-based agentic system. Specialist model capabilities are served through a local FastAPI model server, monitored through callbacks, and reviewed in a role-aware Streamlit dashboard. The result is an inspectable academic system that demonstrates customer-experience decision support with persistence, audit evidence, and reproducible tests.

## 3. Vocabulary to Use

| Term | Meaning in this project |
| --- | --- |
| Customer experience | The quality and relevance of customer interactions across reviews, support, retention, and recommendations |
| Segmentation | Assigning customers to useful groups for targeted decisions |
| Churn risk | Likelihood that a customer may leave or cancel |
| Sentiment | Positive, neutral, or negative customer feedback signal |
| Support intent | The type of help request, such as billing, account, delivery, technical, or general |
| Content strategy | A recommended messaging direction for a customer or segment |
| Recommendation action | Whether a product/action should be recommended, considered, or rejected |
| Orchestration | Coordinating specialist agents and tools in one workflow |
| Auditability | Keeping reviewable records of user actions and runtime events |

## 4. Architecture in Business Language

Use this four-layer explanation:

1. Customer-experience interface  
   The Streamlit dashboard gives reviewers a controlled way to run, inspect, and compare workflows.

2. Agent coordination layer  
   Google ADK coordinates a root agent and specialist agents for the six marketing task families.

3. Specialist intelligence layer  
   DistilBERT, XGBoost, and Qwen LoRA adapters provide focused predictions for text and structured customer data.

4. Evidence layer  
   SQLite and JSONL logs preserve monitoring, demo, cost, session, and audit evidence for later review.

## 5. Problem-Solution-Outcome Story

Problem:

Marketing intelligence is often fragmented. Customer feedback, churn risk, support messages, campaign context, and recommendation evidence may live in separate tools.

Solution:

The system demonstrates a coordinated ADK workflow where specialist tools are called through one agentic interface and reviewed through one dashboard.

Outcome:

Reviewers can inspect customer-experience signals together, see which tools were used, check persistence after page navigation, and run automated tests against critical behaviour.

## 6. Alpha Story

Alpha is a product-company scenario.

Use this phrasing:

> Alpha shows how a product business can combine segmentation, sentiment/churn monitoring, and recommendation action evidence to make more targeted customer-experience decisions.

Avoid saying:

- Alpha sends real campaigns.
- Alpha updates a live ecommerce system.
- Alpha proves production ROI.

## 7. Beta Story

Beta is a service-company scenario.

Use this phrasing:

> Beta shows how a service business can combine churn evidence, support intent routing, and sentiment monitoring to support retention and service-quality review.

Avoid saying:

- Beta contacts real customers.
- Beta updates a live ticketing platform.
- Beta proves operational churn reduction in production.

## 8. Evidence to Mention

Good evidence points:

- model metrics from `experimentation/artifacts/`
- FastAPI model-serving boundary
- ADK callbacks for model/tool events
- SQLite persistence for monitoring, demo, and cost evidence
- JSONL audit records
- role-aware dashboard access
- 29 automated tests under `tests/adk_agent`
- Gemini retry/backoff and pacing for 429 quota errors

## 9. Honest Limitations

State these clearly:

- The system is local and academic.
- External CRM, email, advertising, and social APIs are not connected.
- Demo stories simulate business workflows.
- Cost evidence is Gemini-equivalent for selected local specialist calls, not full infrastructure cost replacement.
- Dashboard authentication is local demo authentication, not enterprise SSO.
- The fine-tuned adapters are specialist components, not general-purpose language models.

## 10. Closing Statement

This project demonstrates how agentic orchestration, local specialist models, model serving, monitoring, and audit evidence can be combined into a digital marketing intelligence system for customer-experience decision support. Its contribution is integration, observability, and reproducibility rather than a new ML algorithm or production marketing platform.
