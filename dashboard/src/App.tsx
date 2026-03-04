import { useEffect, useState } from 'react';
import { ModelUsagePie } from './components/ModelUsagePie';
import { RequestsTimeline } from './components/RequestsTimeline';
import { LatencyBar } from './components/LatencyBar';
import { LogsTable } from './components/LogsTable';
import { fetchSummary, fetchTimeseries, fetchModels, fetchLogs } from './api/client';

interface Summary {
  total_requests: number;
  local_requests: number;
  cloud_requests: number;
  usage_ratio: number;
  total_input_tokens: number;
  total_output_tokens: number;
  estimated_cost: number;
  error_count: number;
  avg_latency_ms: number;
  period_hours: number;
}

interface TimeSeriesData {
  timestamp: string;
  total: number;
  local: number;
  cloud: number;
}

interface ModelData {
  model: string;
  provider: string;
  count: number;
  avg_latency_ms: number;
  total_input_tokens: number;
  total_output_tokens: number;
}

interface LogEntry {
  id: string;
  timestamp: string;
  request_id: string;
  selected_model: string;
  provider: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost: number | null;
  error: string | null;
  routing_reason: string;
}

function App() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [timeseries, setTimeseries] = useState<TimeSeriesData[]>([]);
  const [models, setModels] = useState<ModelData[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [summaryData, timeseriesData, modelsData, logsData] = await Promise.all([
          fetchSummary(),
          fetchTimeseries(),
          fetchModels(),
          fetchLogs(50),
        ]);
        setSummary(summaryData);
        setTimeseries(timeseriesData);
        setModels(modelsData);
        setLogs(logsData.logs);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();

    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div style={styles.loading}>
        <div>Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.error}>
        <h2>Error loading dashboard</h2>
        <p>{error}</p>
        <p style={styles.errorHint}>
          Make sure the OrchexEngine server is running on port 8000.
        </p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>OrchexEngine Dashboard</h1>
        <div style={styles.lastUpdated}>
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </header>

      {summary && (
        <section style={styles.section}>
          <h2 style={styles.sectionTitle}>Summary (Last {summary.period_hours}h)</h2>
          <div style={styles.statsGrid}>
            <StatCard label="Total Requests" value={summary.total_requests} />
            <StatCard label="Local Requests" value={summary.local_requests} />
            <StatCard label="Cloud Requests" value={summary.cloud_requests} />
            <StatCard
              label="Local Usage Ratio"
              value={`${(summary.usage_ratio * 100).toFixed(1)}%`}
            />
            <StatCard
              label="Avg Latency"
              value={`${summary.avg_latency_ms.toFixed(0)}ms`}
            />
            <StatCard
              label="Est. Cost"
              value={`$${summary.estimated_cost.toFixed(4)}`}
            />
            <StatCard label="Errors" value={summary.error_count} isError />
          </div>
        </section>
      )}

      <div style={styles.chartsRow}>
        <section style={styles.chartSection}>
          <h2 style={styles.sectionTitle}>Model Usage Distribution</h2>
          <ModelUsagePie models={models} />
        </section>

        <section style={styles.chartSection}>
          <h2 style={styles.sectionTitle}>Avg Latency by Model</h2>
          <LatencyBar models={models} />
        </section>
      </div>

      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Request Timeline</h2>
        <RequestsTimeline data={timeseries} />
      </section>

      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Recent Requests</h2>
        <LogsTable logs={logs} />
      </section>
    </div>
  );
}

function StatCard({ label, value, isError = false }: { label: string; value: string | number; isError?: boolean }) {
  return (
    <div style={{
      ...styles.statCard,
      ...(isError ? styles.statCardError : {}),
    }}>
      <div style={styles.statLabel}>{label}</div>
      <div style={styles.statValue}>{value}</div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#0f0f1a',
    color: '#e0e0e0',
    padding: '20px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '30px',
    paddingBottom: '20px',
    borderBottom: '1px solid #2a2a3e',
  },
  title: {
    fontSize: '28px',
    fontWeight: '600',
    color: '#ffffff',
  },
  lastUpdated: {
    color: '#888',
    fontSize: '14px',
  },
  loading: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    fontSize: '18px',
    color: '#888',
  },
  error: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    color: '#ff6b6b',
    textAlign: 'center',
  },
  errorHint: {
    color: '#888',
    fontSize: '14px',
    marginTop: '10px',
  },
  section: {
    marginBottom: '30px',
  },
  sectionTitle: {
    fontSize: '18px',
    fontWeight: '500',
    marginBottom: '15px',
    color: '#ffffff',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '15px',
  },
  statCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: '8px',
    padding: '20px',
    textAlign: 'center',
  },
  statCardError: {
    backgroundColor: '#2d1a1a',
  },
  statLabel: {
    fontSize: '12px',
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    marginBottom: '8px',
  },
  statValue: {
    fontSize: '24px',
    fontWeight: '600',
    color: '#ffffff',
  },
  chartsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
    gap: '20px',
    marginBottom: '30px',
  },
  chartSection: {
    backgroundColor: '#1a1a2e',
    borderRadius: '12px',
    padding: '20px',
  },
};

export default App;
