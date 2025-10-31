export type ReasonCode =
  | 'ROBOTS_DISALLOWED'
  | 'CAPTCHA_DETECTED'
  | 'RATE_LIMIT_429'
  | 'HARD_403'
  | 'PARSER_EMPTY'
  | 'SCHEMA_MISSING'
  | 'NEEDS_MANUAL_URL';

export type JobStatus = 'running' | 'pending' | 'completed' | 'failed';

export interface Target {
  id: string;
  domain: string;
  tags: Array<'citations' | 'backlinks' | 'competitor' | 'serp' | 'mentions'>;
  status: 'enabled' | 'disabled';
  lastScrape: string | null;
  robotsStatus: 'ok' | 'disallowed';
  nextRun: string | null;
  depth: number;
  cadence: string;
  renderBudget: number;
  notes?: string;
}

export interface Schedule {
  id: string;
  name: string;
  cron: string;
  enabled: boolean;
  description?: string;
  lastRun?: string | null;
  nextRun?: string | null;
  lastStatus?: string | null;
}

export interface Job {
  id: string;
  type: string;
  domain: string;
  status: JobStatus;
  startedAt: string;
  finishedAt?: string;
  durationSeconds: number;
  reasonCode?: ReasonCode;
  params: Record<string, unknown>;
  logs: string[];
  artifacts: Array<{ id: string; label: string; url: string }>;
}

export interface DashboardResponse {
  trackedDomains: number;
  activeJobs: number;
  queueDepth: number;
  lastRunStatus: 'success' | 'degraded' | 'failing';
  recentEvents: Array<{
    id: string;
    domain: string;
    jobType: string;
    status: JobStatus;
    occurredAt: string;
  }>;
  domainHealth: Array<{
    domain: string;
    lastRun: string;
    robotsStatus: 'ok' | 'disallowed';
    openIssues: number;
  }>;
}

export interface ConfigPayload {
  proxies: Array<{ id?: string; host: string; port: number; username?: string; password?: string }>;
  userAgents: string[];
  rateLimits: {
    globalRpm: number;
    domainConcurrency: number;
  };
  renderBudget: {
    headlessPagesPerHour: number;
  };
  quarantine: {
    retryAfterMinutes: number;
  };
  featureFlags: Record<string, boolean>;
  alerts: {
    email: string[];
    slackWebhooks: string[];
  };
  retention: {
    logsDays: number;
    snapshotsDays: number;
  };
}

export interface LogLine {
  id: string;
  level: 'INFO' | 'WARN' | 'ERROR';
  timestamp: string;
  domain?: string;
  jobId?: string;
  reasonCode?: ReasonCode;
  message: string;
}

export interface LogsResponse {
  items: LogLine[];
  nextCursor?: string;
}

export type StatusLevel = 'ok' | 'warn' | 'error';

export interface StatusCheck {
  id: string;
  name: string;
  status: StatusLevel;
  message: string;
  value?: string | null;
  checkedAt: string;
}

export interface ResourceUsage {
  cpuPercent: number;
  memoryPercent: number;
  diskPercent: number;
  diskFreeBytes: number;
}

export interface IntegrityFinding {
  path: string;
  status: string;
  message: string;
  observedAt: string;
}

export interface WordPressPluginFinding {
  slug: string;
  name: string;
  installedVersion: string;
  latestVersion?: string | null;
  status: string;
  severity: 'info' | 'warning' | 'critical';
  notes?: string | null;
}

export interface WordPressSiteReport {
  site: string;
  baseUrl: string;
  checkedAt: string;
  plugins: WordPressPluginFinding[];
  errors: string[];
}

export interface SystemStatusResponse {
  generatedAt: string;
  checks: StatusCheck[];
  resourceUsage: ResourceUsage;
  lastBackupAt?: string | null;
  lastScraperRunAt?: string | null;
  integrityFindings: IntegrityFinding[];
  wordpress: WordPressSiteReport[];
  logSummary: {
    appErrors: number;
    taskErrors: number;
  };
}

export interface LogTailResponse {
  path: string;
  lines: string[];
  generatedAt: string;
}

export type AlertSeverity = 'info' | 'warning' | 'critical';

export interface AlertItem {
  id: string;
  message: string;
  severity: AlertSeverity;
  source: string;
  createdAt: string;
}

export interface BreadcrumbItem {
  name: string;
  path: string;
}

export interface MediaEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
  modified_at: string;
  mime_type: string | null;
}

export interface MediaListResponse {
  root: 'media' | 'backup';
  path: string;
  breadcrumbs: BreadcrumbItem[];
  entries: MediaEntry[];
}

export interface SnapshotSummary {
  id: string;
  domain: string;
  path: string;
  capturedAt: string;
  hasScreenshot: boolean;
}

export interface SnapshotDetail extends SnapshotSummary {
  html: string;
  screenshotUrl?: string;
}

export interface SnapshotDiffResponse {
  a: SnapshotDetail;
  b: SnapshotDetail;
  diff: string;
}

export interface QuarantineEntry {
  domain: string;
  reason: ReasonCode;
  until: string;
}

export interface ProxyEntry {
  id: string;
  host: string;
  port: number;
  username?: string;
  password?: string;
  lastHealthCheck?: string;
}

export interface UserAgentEntry {
  id: string;
  value: string;
  lastUsed?: string;
}

export interface SaveConfigRequest {
  content: string;
  format: 'json' | 'yaml';
}

export interface PaginatedJobsResponse {
  items: Job[];
}
