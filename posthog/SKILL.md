---
name: posthog
description: Query PostHog analytics — create funnels, trends, insights, and run HogQL queries. Use when the user mentions PostHog, analytics, funnels, events, or user metrics.
allowed-tools: Bash, Read, Write, Glob, Grep
---

# PostHog Skill

Query and manage PostHog analytics: create insights (funnels, trends), run HogQL queries, list events, and check event definitions.

## Trigger

Activate when the user mentions PostHog, analytics dashboards, funnels, conversion rates, event tracking, or user metrics.

## Config

`~/.config/posthog.json`:

```json
{
  "host": "https://us.posthog.com",
  "environments": {
    "dev": {
      "project_id": 395446,
      "api_key": "phx_..."
    },
    "prod": {
      "project_id": 395431,
      "api_key": "phx_..."
    }
  },
  "default_env": "dev"
}
```

Before first use, check if the config exists:

```bash
cat ~/.config/posthog.json 2>/dev/null || echo "MISSING"
```

If missing, ask the user for:
1. **PostHog Host** (default: `https://us.posthog.com`)
2. **Environments** — name, project ID, and Personal API Key for each
3. **Default environment** (used when user doesn't specify)

Then write the config with `Write` tool.

## Environment Selection

- If user says "dev" or "prod", use that environment.
- If user doesn't specify, use `default_env`.
- If user says "both" or "all", run the operation on every environment.

Read config and extract the active environment:

```bash
ENV=${1:-$(python3 -c "import json; print(json.load(open('$HOME/.config/posthog.json'))['default_env'])")}
PROJECT_ID=$(python3 -c "import json; c=json.load(open('$HOME/.config/posthog.json')); print(c['environments']['$ENV']['project_id'])")
API_KEY=$(python3 -c "import json; c=json.load(open('$HOME/.config/posthog.json')); print(c['environments']['$ENV']['api_key'])")
HOST=$(python3 -c "import json; print(json.load(open('$HOME/.config/posthog.json'))['host'])")
```

## Operations

### Create Insight

Create a funnel, trend, or other insight via the API.

**Funnel example:**

```bash
curl -s -X POST "$HOST/api/projects/$PROJECT_ID/insights/" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Funnel",
    "query": {
      "kind": "InsightVizNode",
      "source": {
        "kind": "FunnelsQuery",
        "series": [
          {"kind": "EventsNode", "event": "step_1", "name": "Step 1"},
          {"kind": "EventsNode", "event": "step_2", "name": "Step 2"}
        ],
        "funnelsFilter": {
          "funnelVizType": "steps",
          "funnelWindowInterval": 7,
          "funnelWindowIntervalUnit": "day"
        },
        "dateRange": {"date_from": "-30d"}
      }
    }
  }'
```

**Trend example:**

```bash
curl -s -X POST "$HOST/api/projects/$PROJECT_ID/insights/" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Trend",
    "query": {
      "kind": "InsightVizNode",
      "source": {
        "kind": "TrendsQuery",
        "series": [
          {"kind": "EventsNode", "event": "my_event", "name": "My Event"}
        ],
        "dateRange": {"date_from": "-30d"},
        "interval": "day"
      }
    }
  }'
```

IMPORTANT: Use the new `query` format (InsightVizNode), NOT legacy `filters`. Legacy filters return a permission error.

### Run HogQL Query

Execute ad-hoc SQL-like queries against PostHog data:

```bash
curl -s -X POST "$HOST/api/projects/$PROJECT_ID/query/" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT event, count() FROM events WHERE timestamp > now() - interval 7 day GROUP BY event ORDER BY count() DESC LIMIT 20"
    }
  }'
```

### List Event Definitions

```bash
curl -s "$HOST/api/projects/$PROJECT_ID/event_definitions/?limit=100" \
  -H "Authorization: Bearer $API_KEY"
```

### List Insights

```bash
curl -s "$HOST/api/projects/$PROJECT_ID/insights/?limit=20" \
  -H "Authorization: Bearer $API_KEY"
```

### Get Insight by ID

```bash
curl -s "$HOST/api/projects/$PROJECT_ID/insights/$INSIGHT_ID/" \
  -H "Authorization: Bearer $API_KEY"
```

### Delete Insight

```bash
curl -s -X PATCH "$HOST/api/projects/$PROJECT_ID/insights/$INSIGHT_ID/" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"deleted": true}'
```

## Output

- Always pipe JSON through `python3 -m json.tool` for readability.
- For insight creation, return the insight URL: `$HOST/project/$PROJECT_ID/insights/<short_id>`
- For HogQL queries, format results as a markdown table when possible.
- When creating insights in multiple environments, report each URL.

## Notes

- Personal API Keys (prefix `phx_`) are used, not project API keys (prefix `phc_`).
- The `phc_` keys are for the client SDK event ingestion — they cannot query the API.
- PostHog API base path: `/api/projects/{project_id}/`.
- All timestamps in PostHog are UTC.
