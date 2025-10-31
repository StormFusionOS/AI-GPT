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

export interface IntegrityRecord {
  path: string;
  sha256: string;
  scanned_at: string;
}

export interface IntegrityDrift {
  path: string;
  expected_sha?: string | null;
  observed_sha?: string | null;
  reason: string;
}

export interface SecurityHygieneResponse {
  last_scan: string | null;
  records: IntegrityRecord[];
  drift: IntegrityDrift[];
}

export interface BackupRun {
  id: number;
  run_type: string;
  location: string;
  ok: boolean;
  verify_ok?: boolean | null;
  bytes: number;
  message?: string | null;
  started_at: string;
  finished_at?: string | null;
}

export interface BackupRunListResponse {
  items: BackupRun[];
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

export const fetchSecurityHygiene = async (token: string): Promise<SecurityHygieneResponse> => {
  const { data } = await api.get<SecurityHygieneResponse>('/security/hygiene', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return data;
};

export const triggerSecurityScan = async (token: string): Promise<SecurityHygieneResponse> => {
  const { data } = await api.post<SecurityHygieneResponse>(
    '/security/scan',
    {},
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );
  return data;
};

export const fetchBackupRuns = async (token: string): Promise<BackupRunListResponse> => {
  const { data } = await api.get<BackupRunListResponse>('/backups/runs', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return data;
};

export default api;
