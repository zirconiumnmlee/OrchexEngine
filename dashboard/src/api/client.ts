const API_BASE = '/metrics';

export async function fetchSummary() {
  const res = await fetch(`${API_BASE}/summary`);
  if (!res.ok) throw new Error(`Failed to fetch summary: ${res.statusText}`);
  return res.json();
}

export async function fetchTimeseries(bucketMinutes = 60, hours = 24) {
  const params = new URLSearchParams({
    bucket_minutes: bucketMinutes.toString(),
    hours: hours.toString(),
  });
  const res = await fetch(`${API_BASE}/timeseries?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch timeseries: ${res.statusText}`);
  return res.json();
}

export async function fetchModels(hours = 24) {
  const params = new URLSearchParams({ hours: hours.toString() });
  const res = await fetch(`${API_BASE}/models?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch models: ${res.statusText}`);
  return res.json();
}

export async function fetchLogs(limit = 100, offset = 0, provider?: string) {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
    ...(provider ? { provider } : {}),
  });
  const res = await fetch(`${API_BASE}/logs?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch logs: ${res.statusText}`);
  return res.json();
}
