# User Guide

This guide is for users reviewing or demonstrating the ADK-based Digital Marketing Intelligence System.

## 1. Roles

| Role | Intended user | Main access |
| --- | --- | --- |
| Data Scientist | Technical reviewer or project owner | Full dashboard access, live testing, audit review, reset/clear controls |
| Marketing Manager | Business reviewer | Monitoring, live testing, Alpha/Beta demo execution and review |
| Viewer | Read-only reviewer | Overview, model/tool performance, logs, and completed demo evidence |

Viewer users cannot run live agent queries, execute demo simulations, open the user-audit page, or reset persisted evidence.

## 2. Login

Start the dashboard:

```bash
streamlit run src/adk_agent/dashboard.py
```

Default local demo credentials exist for local-only review if `ADK_DASHBOARD_USERS` is not set. For public or shared demos, always provide your own users through the environment.

| Username | Password | Role |
| --- | --- | --- |
| `admin` | local demo password | Data Scientist |
| `marketing` | local demo password | Marketing Manager |
| `viewer` | local demo password | Viewer |

For public or shared demos, set your own users:

```bash
export ADK_DASHBOARD_USERS="reviewer:<change-me>:viewer,manager:<change-me>:marketing_manager"
```

## 3. Main Dashboard Pages

### System Overview

Use this page for a high-level health check. It shows model calls, tool calls, errors, token usage, Gemini-equivalent cost evidence, cache rate, and persistence status.

### Model Performance

Use this page to inspect model-call latency, token usage, errors, and per-agent metrics captured by ADK callbacks.

### Tool Performance

Use this page to inspect specialist tool calls, latency distributions, success/error status, and call volume.

### Log Explorer

Use this page to review persisted monitoring rows. It is useful for checking what happened during live agent queries and demo runs.

### User Audit

Available to privileged roles only. It shows user-scoped actions such as login, logout, live query execution, reset actions, and audit clears.

### Live Agent Tester

Available to executable roles. It lets a user send a prompt to the ADK root agent. Preset examples cover sentiment, churn, segmentation, support, content, and recommendation workflows.

### Demo Simulation

Runs the Alpha and Beta customer-experience scenarios. Results persist to SQLite so they remain visible after page switches.

### Demo Performance Dashboard

Shows demo-specific monitoring, cost evidence, latency, token usage, and persisted story summaries.

### Demo Before vs After Impact

Compares manual marketing operations with the system-supported workflow using model evidence, latency evidence, and traceability.

### Demo Log Explorer

Shows the event-level trail created during Alpha/Beta scenario runs.

### Demo System Architecture

Explains the relationship between Streamlit, ADK, FastAPI, local model artefacts, and persistent evidence stores.

## 4. Alpha Scenario

Alpha is a product-company scenario. It demonstrates how the system can support customer experience by combining:

- segmentation evidence
- sentiment/churn monitoring
- recommendation action classification
- persisted traces and cost evidence

Alpha does not send real campaigns or update live ecommerce systems.

## 5. Beta Scenario

Beta is a service-company scenario. It demonstrates how the system can support customer retention and support quality by combining:

- structured and text-based churn evidence
- support intent routing
- crisis sentiment monitoring
- persisted traces and cost evidence

Beta does not contact real customers or send outbound messages.

## 6. Common User Tasks

Run a product-company demonstration:

1. Login as Data Scientist or Marketing Manager.
2. Open `Demo Simulation`.
3. Click `Run Alpha Story`.
4. Review output tables.
5. Open `Demo Performance Dashboard` and `Demo Log Explorer`.

Run a service-company demonstration:

1. Login as Data Scientist or Marketing Manager.
2. Open `Demo Simulation`.
3. Click `Run Beta Story`.
4. Review churn, support, and sentiment outputs.
5. Check persisted monitoring and cost evidence.

Review evidence only:

1. Login as Viewer.
2. Open `System Overview`, `Model Performance`, or `Log Explorer`.
3. Review completed demo evidence without executing new workflows.

## 7. Safety Boundaries

The current system is for academic and local demonstration use. It does not provide:

- enterprise SSO
- production secret management
- live CRM writes
- live email/social dispatch
- live advertising-platform integration
- automated retraining in production

Audit logs and monitoring records are included to make the demonstration traceable, not to claim full enterprise compliance.
