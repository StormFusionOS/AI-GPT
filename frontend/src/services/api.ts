import axios from 'axios';
import type {
  AlertItem,
  ConfigPayload,
  DashboardResponse,
  Job,
  LogTailResponse,
  LogsResponse,
  MediaListResponse,
  PaginatedJobsResponse,
  ProxyEntry,
  QuarantineEntry,
  Schedule,
  SnapshotDetail,
  SnapshotDiffResponse,
  SnapshotSummary,
  SystemStatusResponse,
  Target,
  UserAgentEntry,
} from '@/types';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
});

apiClient.interceptors.request.use((config) => {
  config.headers = config.headers ?? {};
  config.headers['Content-Type'] = 'application/json';
  if (!config.headers['X-User-Role']) {
    config.headers['X-User-Role'] = 'admin';
  }
  return config;
});

export const api = {
  getDashboard: async (): Promise<DashboardResponse> => {
    const { data } = await apiClient.get<DashboardResponse>('/dashboard');
    return data;
  },
  getTargets: async (): Promise<Target[]> => {
    const { data } = await apiClient.get<Target[]>('/targets');
    return data;
  },
  createTarget: async (payload: Partial<Target>): Promise<Target> => {
    const { data } = await apiClient.post<Target>('/targets', payload);
    return data;
  },
  updateTarget: async (id: string, payload: Partial<Target>): Promise<Target> => {
    const { data } = await apiClient.put<Target>(`/targets/${id}`, payload);
    return data;
  },
  runTarget: async (id: string): Promise<void> => {
    await apiClient.post(`/targets/${id}/run`, {});
  },
  getSchedules: async (): Promise<Schedule[]> => {
    const { data } = await apiClient.get<Schedule[]>('/schedules');
    return data;
  },
  toggleSchedule: async (id: string, enabled: boolean): Promise<Schedule> => {
    const { data } = await apiClient.post<Schedule>(`/schedules/${id}/toggle`, { enabled });
    return data;
  },
  runScheduleNow: async (id: string): Promise<Schedule> => {
    const { data } = await apiClient.post<Schedule>(`/schedules/${id}/run`, {});
    return data;
  },
  getJobs: async (status: string): Promise<PaginatedJobsResponse> => {
    const { data } = await apiClient.get<PaginatedJobsResponse>('/jobs', { params: { status } });
    return data;
  },
  getJob: async (id: string): Promise<Job> => {
    const { data } = await apiClient.get<Job>(`/jobs/${id}`);
    return data;
  },
  retryJob: async (id: string): Promise<void> => {
    await apiClient.post(`/jobs/${id}/retry`, {});
  },
  cancelJob: async (id: string): Promise<void> => {
    await apiClient.post(`/jobs/${id}/cancel`, {});
  },
  getConfig: async (): Promise<ConfigPayload> => {
    const { data } = await apiClient.get<ConfigPayload>('/config');
    return data;
  },
  saveConfig: async (payload: ConfigPayload): Promise<ConfigPayload> => {
    const { data } = await apiClient.put<ConfigPayload>('/config', payload);
    return data;
  },
  getLogs: async (params: Record<string, string | undefined>): Promise<LogsResponse> => {
    const { data } = await apiClient.get<LogsResponse>('/logs', { params });
    return data;
  },
  getSnapshots: async (params?: { domain?: string }): Promise<SnapshotSummary[]> => {
    const { data } = await apiClient.get<SnapshotSummary[]>('/snapshots', { params });
    return data;
  },
  getSnapshot: async (id: string): Promise<SnapshotDetail> => {
    const { data } = await apiClient.get<SnapshotDetail>(`/snapshots/${id}`);
    return data;
  },
  getSnapshotDiff: async (a: string, b: string): Promise<SnapshotDiffResponse> => {
    const { data } = await apiClient.get<SnapshotDiffResponse>('/snapshots/diff', {
      params: { a, b },
    });
    return data;
  },
  getQuarantine: async (): Promise<QuarantineEntry[]> => {
    const { data } = await apiClient.get<QuarantineEntry[]>('/quarantine');
    return data;
  },
  releaseDomain: async (domain: string): Promise<void> => {
    await apiClient.post(`/quarantine/${encodeURIComponent(domain)}/release`, {});
  },
  extendQuarantine: async (domain: string): Promise<void> => {
    await apiClient.post(`/quarantine/${encodeURIComponent(domain)}/extend`, {});
  },
  getProxies: async (): Promise<ProxyEntry[]> => {
    const { data } = await apiClient.get<ProxyEntry[]>('/proxies');
    return data;
  },
  saveProxies: async (proxies: ProxyEntry[]): Promise<ProxyEntry[]> => {
    const { data } = await apiClient.put<ProxyEntry[]>('/proxies', { proxies });
    return data;
  },
  getUserAgents: async (): Promise<UserAgentEntry[]> => {
    const { data } = await apiClient.get<UserAgentEntry[]>('/user-agents');
    return data;
  },
  saveUserAgents: async (items: UserAgentEntry[]): Promise<UserAgentEntry[]> => {
    const { data } = await apiClient.put<UserAgentEntry[]>('/user-agents', { userAgents: items });
    return data;
  },
  getMediaList: async ({ root, path }: { root: 'media' | 'backup'; path?: string }): Promise<MediaListResponse> => {
    const { data } = await apiClient.get<MediaListResponse>('/media/list', { params: { root, path } });
    return data;
  },
  fetchMediaFile: async ({
    root,
    path,
    responseType = 'blob',
  }: {
    root: 'media' | 'backup';
    path: string;
    responseType?: 'blob' | 'arraybuffer' | 'text';
  }): Promise<Blob | ArrayBuffer | string> => {
    const encodedPath = path
      .split('/')
      .filter(Boolean)
      .map(encodeURIComponent)
      .join('/');
    const response = await apiClient.get(`/media/file/${encodedPath}`, {
      params: { root },
      responseType,
    });
    return response.data;
  },
  getMediaDownloadUrl: ({ root, path }: { root: 'media' | 'backup'; path: string }): string => {
    const base = apiClient.defaults.baseURL ?? '';
    const normalizedBase = base.endsWith('/') ? base.slice(0, -1) : base;
    const encodedPath = path
      .split('/')
      .filter(Boolean)
      .map(encodeURIComponent)
      .join('/');
    return `${normalizedBase}/media/file/${encodedPath}?root=${root}`;
  },
  getSystemStatus: async (): Promise<SystemStatusResponse> => {
    const { data } = await apiClient.get<SystemStatusResponse>('/status');
    return data;
  },
  getAppLogTail: async (lines: number): Promise<LogTailResponse> => {
    const { data } = await apiClient.get<LogTailResponse>('/logs/app', { params: { lines } });
    return data;
  },
  getTaskLogTail: async (lines: number): Promise<LogTailResponse> => {
    const { data } = await apiClient.get<LogTailResponse>('/logs/tasks', { params: { lines } });
    return data;
  },
  getAlerts: async (): Promise<AlertItem[]> => {
    const { data } = await apiClient.get<AlertItem[]>('/alerts');
    return data;
  },
  acknowledgeAlert: async (id: string): Promise<void> => {
    await apiClient.post(`/alerts/${id}/acknowledge`, {});
  },
};

export type ApiClient = typeof api;
