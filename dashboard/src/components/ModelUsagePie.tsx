export interface ModelData {
  model: string;
  provider: string;
  count: number;
  avg_latency_ms: number;
  total_input_tokens: number;
  total_output_tokens: number;
}

interface ModelUsagePieProps {
  models: ModelData[];
}

export function ModelUsagePie({ models }: ModelUsagePieProps) {
  const data = models.map((m) => ({
    name: m.model.split('/').pop() || m.model,
    value: m.count,
    provider: m.provider,
  }));

  if (data.length === 0) {
    return <div style={styles.empty}>No data available</div>;
  }

  return (
    <div style={styles.container}>
      <div style={styles.legend}>
        {data.map((item, index) => (
          <div key={index} style={styles.legendItem}>
            <div
              style={{
                ...styles.legendColor,
                backgroundColor: getColor(index, item.provider),
              }}
            />
            <span style={styles.legendLabel}>
              {item.name} ({item.value})
            </span>
          </div>
        ))}
      </div>
      <div style={styles.pieContainer}>
        <SimplePieChart data={data} />
      </div>
    </div>
  );
}

function SimplePieChart({ data }: { data: { name: string; value: number; provider: string }[] }) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  let currentAngle = 0;

  const slices = data.map((d, i) => {
    const angle = (d.value / total) * 360;
    const startAngle = currentAngle;
    currentAngle += angle;

    const startRad = (startAngle - 90) * (Math.PI / 180);
    const endRad = (startAngle + angle - 90) * (Math.PI / 180);

    const x1 = 100 + 80 * Math.cos(startRad);
    const y1 = 100 + 80 * Math.sin(startRad);
    const x2 = 100 + 80 * Math.cos(endRad);
    const y2 = 100 + 80 * Math.sin(endRad);

    const largeArc = angle > 180 ? 1 : 0;

    const pathData = [
      `M 100 100`,
      `L ${x1} ${y1}`,
      `A 80 80 0 ${largeArc} 1 ${x2} ${y2}`,
      `Z`,
    ].join(' ');

    return (
      <path
        key={i}
        d={pathData}
        fill={getColor(i, d.provider)}
        stroke="#1a1a2e"
        strokeWidth="2"
      />
    );
  });

  return (
    <svg viewBox="0 0 200 200" style={styles.svg}>
      {slices}
    </svg>
  );
}

function getColor(index: number, provider: string): string {
  const localColors = ['#4ade80', '#22d3ee', '#818cf8'];
  const cloudColors = ['#f87171', '#fb923c', '#facc15'];
  const colors = provider === 'local' ? localColors : cloudColors;
  return colors[index % colors.length];
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '10px',
  },
  legend: {
    display: 'flex',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: '15px',
    marginBottom: '20px',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  legendColor: {
    width: '14px',
    height: '14px',
    borderRadius: '3px',
  },
  legendLabel: {
    fontSize: '13px',
    color: '#e0e0e0',
  },
  pieContainer: {
    display: 'flex',
    justifyContent: 'center',
  },
  svg: {
    maxWidth: '200px',
    maxHeight: '200px',
  },
  empty: {
    textAlign: 'center',
    color: '#666',
    padding: '40px',
  },
};
