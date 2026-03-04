interface ModelData {
  model: string;
  provider: string;
  count: number;
  avg_latency_ms: number;
  total_input_tokens: number;
  total_output_tokens: number;
}

interface LatencyBarProps {
  models: ModelData[];
}

export function LatencyBar({ models }: LatencyBarProps) {
  if (models.length === 0) {
    return <div style={styles.empty}>No data available</div>;
  }

  const maxLatency = Math.max(...models.map((m) => m.avg_latency_ms), 1);

  return (
    <div style={styles.container}>
      {models.map((model, index) => {
        const barWidth = (model.avg_latency_ms / maxLatency) * 100;
        const modelName = model.model.split('/').pop() || model.model;

        return (
          <div key={index} style={styles.row}>
            <div style={styles.label}>
              <span style={styles.modelName}>{modelName}</span>
              <span style={styles.provider}>{model.provider}</span>
            </div>
            <div style={styles.barWrapper}>
              <div
                style={{
                  ...styles.bar,
                  width: `${barWidth}%`,
                  backgroundColor: model.provider === 'local' ? '#4ade80' : '#f87171',
                }}
              />
            </div>
            <div style={styles.value}>
              {model.avg_latency_ms.toFixed(0)}ms
            </div>
          </div>
        );
      })}
      <div style={styles.legend}>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, backgroundColor: '#4ade80' }} />
          Local
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, backgroundColor: '#f87171' }} />
          Cloud
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '10px',
  },
  row: {
    display: 'flex',
    alignItems: 'center',
    marginBottom: '12px',
  },
  label: {
    width: '120px',
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  modelName: {
    fontSize: '13px',
    color: '#e0e0e0',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  provider: {
    fontSize: '11px',
    color: '#666',
    textTransform: 'uppercase',
  },
  barWrapper: {
    flex: 1,
    height: '20px',
    backgroundColor: '#2a2a3e',
    borderRadius: '4px',
    overflow: 'hidden',
    margin: '0 10px',
  },
  bar: {
    height: '100%',
    borderRadius: '4px',
    transition: 'width 0.3s ease',
  },
  value: {
    width: '70px',
    textAlign: 'right',
    fontSize: '13px',
    color: '#e0e0e0',
    fontFamily: 'monospace',
  },
  legend: {
    display: 'flex',
    justifyContent: 'center',
    gap: '20px',
    marginTop: '15px',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '13px',
    color: '#e0e0e0',
  },
  legendDot: {
    width: '12px',
    height: '12px',
    borderRadius: '2px',
  },
  empty: {
    textAlign: 'center',
    color: '#666',
    padding: '40px',
  },
};
