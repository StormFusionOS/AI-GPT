import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_OPS_API_URL ?? 'http://localhost:8001/api/v1',
});

export interface ServiceHealth {
  service: string;
  status: 'ok' | 'warn' | 'down';
  latency_ms: number | null;
  checked_at: string;
  details?: Record<string, unknown> | null;
}

export interface TaskRun {
  id: number;
  module: string;
  task: string;
  status: string;
  queued_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  retries: number;
  message?: string | null;
}

export interface OrchestratorHealthResponse {
  services: ServiceHealth[];
  generated_at: string;
}

export interface TaskRunListResponse {
  items: TaskRun[];
}

export const fetchHealth = async (token: string): Promise<OrchestratorHealthResponse> => {
  const { data } = await api.get<OrchestratorHealthResponse>('/orchestrator/health', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return data;
};

export const fetchTasks = async (
  token: string,
  params?: { module?: string; status?: string }
): Promise<TaskRunListResponse> => {
  const { data } = await api.get<TaskRunListResponse>('/orchestrator/tasks', {
    headers: { Authorization: `Bearer ${token}` },
    params,
  });
  return data;
};

export const dispatchTask = async (
  token: string,
  name: string,
  payload: Record<string, unknown>
): Promise<void> => {
  await api.post(
    '/orchestrator/dispatch',
    { name, payload },
    { headers: { Authorization: `Bearer ${token}` } }
  );
};

export default api;
