# OrchexEngine Dashboard

React-based dashboard for visualizing OrchexEngine telemetry data.

## Features

- **Summary Stats**: Total requests, local/cloud usage ratio, latency, costs, errors
- **Model Usage Pie**: Distribution of requests across models
- **Request Timeline**: Time-series view of local vs cloud requests
- **Latency Comparison**: Average latency by model
- **Request Logs**: Paginated table of recent requests with routing reasons

## Setup

```bash
# Install dependencies
npm install

# Start development server (proxy to backend on port 8000)
npm run dev

# Build for production
npm run build
```

Access the dashboard at http://localhost:5173

## API Client

The dashboard proxies requests to the OrchexEngine backend via Vite config:

```typescript
// src/api/client.ts
fetch('/metrics/summary')  // -> http://localhost:8000/metrics/summary
```

## Components

| Component | Description |
|-----------|-------------|
| `ModelUsagePie` | Pie chart showing model distribution |
| `RequestsTimeline` | Stacked bar chart (local/cloud over time) |
| `LatencyBar` | Horizontal bar chart of avg latency by model |
| `LogsTable` | Paginated table of request logs |

## Styling

Dark theme with custom CSS-in-JS (no external CSS framework).
Charts are custom SVG implementations (no Recharts dependency required for MVP).
