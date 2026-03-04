interface TimeSeriesData {
  timestamp: string;
  total: number;
  local: number;
  cloud: number;
}

interface RequestsTimelineProps {
  data: TimeSeriesData[];
}

export function RequestsTimeline({ data }: RequestsTimelineProps) {
  if (data.length === 0) {
    return <div style={styles.empty}>No data available</div>;
  }

  const maxRequests = Math.max(...data.map((d) => d.total), 1);

  // Format timestamp for display
  const formatTime = (ts: string) => {
    const date = new Date(ts);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div style={styles.container}>
      <div style={styles.chart}>
        {data.map((point, index) => {
          const localHeight = (point.local / maxRequests) * 100;
          const cloudHeight = (point.cloud / maxRequests) * 100;

          return (
            <div key={index} style={styles.barContainer}>
              <div style={styles.barStack}>
                <div
                  style={{
                    ...styles.barSegment,
                    height: `${localHeight}%`,
                    backgroundColor: '#4ade80',
                  }}
                  title={`Local: ${point.local}`}
                />
                <div
                  style={{
                    ...styles.barSegment,
                    height: `${cloudHeight}%`,
                    backgroundColor: '#f87171',
                  }}
                  title={`Cloud: ${point.cloud}`}
                />
              </div>
              <div style={styles.timeLabel}>{formatTime(point.timestamp)}</div>
            </div>
          );
        })}
      </div>
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
  chart: {
    display: 'flex',
    alignItems: 'flex-end',
    justifyContent: 'space-around',
    height: '200px',
    gap: '4px',
    paddingBottom: '25px',
    borderBottom: '1px solid #333',
  },
  barContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    flex: 1,
  },
  barStack: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'flex-end',
    width: '100%',
    maxHeight: '160px',
  },
  barSegment: {
    minHeight: '2px',
    transition: 'height 0.3s ease',
  },
  timeLabel: {
    fontSize: '10px',
    color: '#666',
    marginTop: '4px',
    transform: 'rotate(-45deg)',
    transformOrigin: 'left top',
    whiteSpace: 'nowrap',
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
