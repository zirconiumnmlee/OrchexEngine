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

interface LogsTableProps {
  logs: LogEntry[];
}

export function LogsTable({ logs }: LogsTableProps) {
  if (logs.length === 0) {
    return <div style={styles.empty}>No logs available</div>;
  }

  const formatTime = (ts: string) => {
    const date = new Date(ts);
    return date.toLocaleString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatModel = (model: string) => {
    return model.split('/').pop() || model;
  };

  return (
    <div style={styles.container}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>Time</th>
            <th style={styles.th}>Provider</th>
            <th style={styles.th}>Model</th>
            <th style={styles.th}>Latency</th>
            <th style={styles.th}>Tokens</th>
            <th style={styles.th}>Reason</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr
              key={log.id}
              style={{
                ...styles.tr,
                ...(log.error ? styles.errorRow : {}),
              }}
            >
              <td style={styles.td}>{formatTime(log.timestamp)}</td>
              <td style={styles.td}>
                <span
                  style={{
                    ...styles.badge,
                    backgroundColor:
                      log.provider === 'local' ? '#22c55e33' : '#ef444433',
                    color: log.provider === 'local' ? '#4ade80' : '#f87171',
                  }}
                >
                  {log.provider}
                </span>
              </td>
              <td style={styles.td}>{formatModel(log.selected_model)}</td>
              <td style={{ ...styles.td, fontFamily: 'monospace' }}>
                {log.latency_ms}ms
              </td>
              <td style={{ ...styles.td, fontFamily: 'monospace', fontSize: '12px' }}>
                {log.input_tokens}/{log.output_tokens}
              </td>
              <td style={{ ...styles.td, maxWidth: '200px' }} title={log.routing_reason}>
                {truncate(log.routing_reason, 40)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function truncate(str: string, len: number): string {
  if (str.length <= len) return str;
  return str.slice(0, len - 3) + '...';
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '13px',
  },
  th: {
    textAlign: 'left',
    padding: '12px 8px',
    borderBottom: '1px solid #333',
    color: '#888',
    fontWeight: '500',
    textTransform: 'uppercase',
    fontSize: '11px',
    letterSpacing: '0.5px',
  },
  tr: {
    borderBottom: '1px solid #2a2a3e',
  },
  td: {
    padding: '10px 8px',
    color: '#e0e0e0',
  },
  badge: {
    padding: '3px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    fontWeight: '500',
    textTransform: 'uppercase',
  },
  errorRow: {
    backgroundColor: '#2d1a1a55',
  },
  empty: {
    textAlign: 'center',
    color: '#666',
    padding: '40px',
  },
};
