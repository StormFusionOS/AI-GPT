import { http, HttpResponse, delay } from 'msw';
import type {
  AlertItem,
  ConfigPayload,
  DashboardResponse,
  Job,
  JobStatus,
  LogLine,
  LogTailResponse,
  MediaListResponse,
  PaginatedJobsResponse,
  ProxyEntry,
  QuarantineEntry,
  Schedule,
  SnapshotDetail,
  SnapshotSummary,
  SystemStatusResponse,
  Target,
  UserAgentEntry,
} from '@/types';

const API_BASE = import.meta.env.VITE_API_URL ?? '/api';
const NETWORK_DELAY = 300;

const createId = (prefix: string) => `${prefix}-${Math.random().toString(36).slice(2, 10)}`;

const dashboard: DashboardResponse = {
  trackedDomains: 48,
  activeJobs: 6,
  queueDepth: 14,
  lastRunStatus: 'success',
  recentEvents: [
    { id: createId('evt'), domain: 'rivercityclean.com', jobType: 'SERP_SAMPLER_DAILY', status: 'completed', occurredAt: new Date().toISOString() },
    { id: createId('evt'), domain: 'competitorcleaners.com', jobType: 'BACKLINK_MONITOR_WEEKLY', status: 'running', occurredAt: new Date(Date.now() - 1000 * 60 * 12).toISOString() },
    { id: createId('evt'), domain: 'spotlessseattle.com', jobType: 'CITATIONS_DELTA_DAILY', status: 'failed', occurredAt: new Date(Date.now() - 1000 * 60 * 45).toISOString() },
  ],
  domainHealth: [
    { domain: 'rivercityclean.com', lastRun: new Date().toISOString(), robotsStatus: 'ok', openIssues: 1 },
    { domain: 'spotlessseattle.com', lastRun: new Date(Date.now() - 86400000).toISOString(), robotsStatus: 'ok', openIssues: 3 },
    { domain: 'pristinepros.co', lastRun: new Date(Date.now() - 2 * 86400000).toISOString(), robotsStatus: 'disallowed', openIssues: 5 },
    { domain: 'competitorcleaners.com', lastRun: new Date(Date.now() - 3600000).toISOString(), robotsStatus: 'ok', openIssues: 0 },
  ],
};

let systemStatusSnapshot: SystemStatusResponse = {
  generatedAt: new Date().toISOString(),
  checks: [
    { id: 'database', name: 'PostgreSQL', status: 'ok', message: 'Responded in 14.2 ms', value: '14.2 ms', checkedAt: new Date().toISOString() },
    { id: 'qdrant', name: 'Qdrant', status: 'ok', message: '5 collections available', value: '5', checkedAt: new Date().toISOString() },
    { id: 'redis', name: 'Redis Broker', status: 'ok', message: 'Broker reachable', checkedAt: new Date().toISOString() },
    { id: 'disk', name: 'Disk Usage', status: 'warn', message: '78.1% used', value: '78.1%', checkedAt: new Date().toISOString() },
  ],
  resourceUsage: {
    cpuPercent: 46.5,
    memoryPercent: 63.2,
    diskPercent: 78.1,
    diskFreeBytes: 320 * 1024 * 1024 * 1024,
  },
  lastBackupAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
  lastScraperRunAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  integrityFindings: [
    {
      path: '/app/config/.env',
      status: 'changed',
      message: 'Checksum differs from baseline',
      observedAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    },
  ],
  wordpress: [
    {
      site: 'River City Clean',
      baseUrl: 'https://rivercityclean.com',
      checkedAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      plugins: [
        {
          slug: 'seo-by-rivercity',
          name: 'SEO Enhancer',
          installedVersion: '1.2.0',
          latestVersion: '1.4.0',
          status: 'outdated',
          severity: 'warning',
          notes: 'Update recommended',
        },
        {
          slug: 'wordfence',
          name: 'Wordfence Security',
          installedVersion: '7.10.0',
          latestVersion: '7.10.0',
          status: 'ok',
          severity: 'info',
          notes: null,
        },
      ],
      errors: [],
    },
  ],
  logSummary: { appErrors: 1, taskErrors: 0 },
};

let appLogTail: LogTailResponse = {
  path: '/var/log/app.log',
  generatedAt: new Date().toISOString(),
  lines: [
    '2024-02-10T16:32:11Z [INFO] started background task',
    '2024-02-10T16:32:12Z [INFO] fetching SERP snapshot for "carpet cleaning boise"',
    '2024-02-10T16:32:13Z [WARN] transient SERP API warning: HTTP 429, retrying',
    '2024-02-10T16:32:16Z [INFO] recovered from rate limit backoff',
  ],
};

let taskLogTail: LogTailResponse = {
  path: '/var/log/tasks.log',
  generatedAt: new Date().toISOString(),
  lines: [
    '2024-02-10T15:12:01Z [INFO] starting backup workflow',
    '2024-02-10T15:12:08Z [INFO] pg_dump complete',
    '2024-02-10T15:12:45Z [INFO] media archive created (120MB)',
    '2024-02-10T15:13:10Z [INFO] rotation complete, retained 7 archives',
  ],
};

let activeAlerts: AlertItem[] = [
  {
    id: 'alert-disk',
    message: 'Disk usage above 75% threshold',
    severity: 'warning',
    source: 'status:disk',
    createdAt: new Date(Date.now() - 20 * 60 * 1000).toISOString(),
  },
  {
    id: 'alert-backup',
    message: 'No backup detected in the last 36 hours',
    severity: 'critical',
    source: 'backup',
    createdAt: new Date(Date.now() - 40 * 60 * 1000).toISOString(),
  },
];

function refreshSystemStatus(): SystemStatusResponse {
  const now = new Date();
  systemStatusSnapshot = {
    ...systemStatusSnapshot,
    generatedAt: now.toISOString(),
    checks: systemStatusSnapshot.checks.map((check) => ({ ...check, checkedAt: now.toISOString() })),
    resourceUsage: {
      ...systemStatusSnapshot.resourceUsage,
      cpuPercent: Number((40 + Math.random() * 20).toFixed(1)),
      memoryPercent: Number((55 + Math.random() * 15).toFixed(1)),
    },
    logSummary: {
      appErrors: appLogTail.lines.filter((line) => /ERROR|Exception|WARN/.test(line)).length,
      taskErrors: taskLogTail.lines.filter((line) => /ERROR|Exception|WARN/.test(line)).length,
    },
  };
  appLogTail = { ...appLogTail, generatedAt: now.toISOString() };
  taskLogTail = { ...taskLogTail, generatedAt: now.toISOString() };
  return systemStatusSnapshot;
}

let targets: Target[] = [
  {
    id: createId('tgt'),
    domain: 'rivercityclean.com',
    tags: ['citations', 'serp'],
    status: 'enabled',
    lastScrape: new Date(Date.now() - 3600000).toISOString(),
    robotsStatus: 'ok',
    nextRun: new Date(Date.now() + 3600000).toISOString(),
    depth: 3,
    cadence: '0 */2 * * *',
    renderBudget: 10,
    notes: 'Primary site',
  },
  {
    id: createId('tgt'),
    domain: 'competitorcleaners.com',
    tags: ['competitor', 'backlinks'],
    status: 'enabled',
    lastScrape: new Date(Date.now() - 7200000).toISOString(),
    robotsStatus: 'ok',
    nextRun: new Date(Date.now() + 7200000).toISOString(),
    depth: 2,
    cadence: '30 1 * * *',
    renderBudget: 6,
    notes: 'Competitor monitoring',
  },
  {
    id: createId('tgt'),
    domain: 'spotlessseattle.com',
    tags: ['citations', 'mentions'],
    status: 'disabled',
    lastScrape: new Date(Date.now() - 86400000).toISOString(),
    robotsStatus: 'disallowed',
    nextRun: null,
    depth: 2,
    cadence: '0 3 * * *',
    renderBudget: 4,
    notes: 'Robots change pending',
  },
];

let schedules: Schedule[] = [
  {
    id: 'CITATIONS_DELTA_DAILY',
    name: 'Citations Delta Daily',
    cron: '0 1 * * *',
    enabled: true,
    description: 'Checks directories for new NAP changes.',
    lastRun: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    nextRun: new Date(Date.now() + 20 * 60 * 60 * 1000).toISOString(),
    lastStatus: 'success',
  },
  {
    id: 'BACKLINK_MONITOR_WEEKLY',
    name: 'Backlink Monitor Weekly',
    cron: '0 3 * * 1',
    enabled: true,
    description: 'Fetches backlink updates for tracked domains.',
    lastRun: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    nextRun: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
    lastStatus: 'success',
  },
  {
    id: 'RENDER_CHECK_WEEKLY',
    name: 'Render Check Weekly',
    cron: '30 4 * * 1',
    enabled: false,
    description: 'Validates JS-required pages still render correctly.',
    lastRun: null,
    nextRun: null,
    lastStatus: 'disabled',
  },
  {
    id: 'SERP_SAMPLER_DAILY',
    name: 'SERP Sampler Daily',
    cron: '15 * * * *',
    enabled: true,
    description: 'Captures SERP snapshots for key keywords.',
    lastRun: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    nextRun: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
    lastStatus: 'queued',
  },
];

const jobStore: Record<JobStatus, Job[]> = {
  running: [
    {
      id: createId('job'),
      type: 'SERP_FETCH',
      domain: 'rivercityclean.com',
      status: 'running',
      startedAt: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
      durationSeconds: 300,
      params: { keyword: 'house cleaning boise', region: 'US-ID' },
      logs: ['Starting SERP fetch', 'Fetching Google results…'],
      artifacts: [],
    },
  ],
  pending: [
    {
      id: createId('job'),
      type: 'BACKLINK_CRAWL',
      domain: 'competitorcleaners.com',
      status: 'pending',
      startedAt: new Date().toISOString(),
      durationSeconds: 0,
      params: { depth: 2 },
      logs: [],
      artifacts: [],
    },
  ],
  completed: [
    {
      id: createId('job'),
      type: 'CITATION_SYNC',
      domain: 'rivercityclean.com',
      status: 'completed',
      startedAt: new Date(Date.now() - 3600000).toISOString(),
      durationSeconds: 180,
      params: { directory: 'Yelp' },
      logs: ['Syncing Yelp listing', 'No changes detected'],
      artifacts: [],
    },
  ],
  failed: [
    {
      id: createId('job'),
      type: 'MENTIONS_DISCOVERY',
      domain: 'spotlessseattle.com',
      status: 'failed',
      startedAt: new Date(Date.now() - 2 * 3600000).toISOString(),
      durationSeconds: 90,
      params: { keyword: 'spotless seattle reviews' },
      reasonCode: 'RATE_LIMIT_429',
      logs: ['Queueing queries…', 'Got 429, scheduling retry'],
      artifacts: [{ id: createId('artifact'), label: 'SERP screenshot', url: 'https://placehold.co/600x400?text=SERP' }],
    },
  ],
};

let config: ConfigPayload = {
  proxies: [
    { id: createId('pxy'), host: 'proxy1.scraper.local', port: 3128, username: 'crawler', password: 'secret', lastHealthCheck: new Date().toISOString() },
    { id: createId('pxy'), host: 'proxy2.scraper.local', port: 3128, username: 'crawler', password: 'secret', lastHealthCheck: new Date(Date.now() - 3600000).toISOString() },
  ],
  userAgents: ['Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'],
  rateLimits: { globalRpm: 120, domainConcurrency: 3 },
  renderBudget: { headlessPagesPerHour: 80 },
  quarantine: { retryAfterMinutes: 90 },
  featureFlags: { enable_serp_screenshot: true, enable_proxy_failover: false },
  alerts: { email: ['ops@scraper.dev'], slackWebhooks: ['https://hooks.slack.com/services/FAKE/WEBHOOK'] },
  retention: { logsDays: 30, snapshotsDays: 120 },
};

let logs: LogLine[] = Array.from({ length: 25 }).map((_, index) => {
  const level = index % 7 === 0 ? 'ERROR' : index % 4 === 0 ? 'WARN' : 'INFO';
  return {
    id: createId('log'),
    level,
    timestamp: new Date(Date.now() - index * 60000).toISOString(),
    domain: ['rivercityclean.com', 'spotlessseattle.com', 'competitorcleaners.com'][index % 3],
    jobId: jobStore.running[0]?.id,
    reasonCode: level === 'ERROR' ? 'RATE_LIMIT_429' : undefined,
    message: level === 'ERROR' ? 'Exceeded provider rate limit' : `Log entry ${index}`,
  };
});

const snapshotDetails: SnapshotDetail[] = [
  {
    id: createId('snap'),
    domain: 'rivercityclean.com',
    path: '/services',
    capturedAt: new Date(Date.now() - 3600000).toISOString(),
    hasScreenshot: true,
    html: '<html><body><h1>Services</h1><p>River City Cleaning offers eco-friendly options.</p></body></html>',
    screenshotUrl: 'https://placehold.co/800x600?text=Services',
  },
  {
    id: createId('snap'),
    domain: 'rivercityclean.com',
    path: '/services',
    capturedAt: new Date(Date.now() - 2 * 3600000).toISOString(),
    hasScreenshot: true,
    html: '<html><body><h1>Services</h1><p>River City Cleaning offers standard packages.</p></body></html>',
    screenshotUrl: 'https://placehold.co/800x600?text=Services+Old',
  },
  {
    id: createId('snap'),
    domain: 'spotlessseattle.com',
    path: '/',
    capturedAt: new Date(Date.now() - 86400000).toISOString(),
    hasScreenshot: false,
    html: '<html><body><h1>Spotless Seattle</h1><p>Quality cleaning for Seattle businesses.</p></body></html>',
  },
];

let quarantine: QuarantineEntry[] = [
  { domain: 'blocked-example.com', reason: 'CAPTCHA_DETECTED', until: new Date(Date.now() + 6 * 3600000).toISOString() },
  { domain: 'aggressive-competitor.com', reason: 'HARD_403', until: new Date(Date.now() + 12 * 3600000).toISOString() },
];

let proxies: ProxyEntry[] = config.proxies;
let userAgents: UserAgentEntry[] = config.userAgents.map((value) => ({ id: createId('ua'), value, lastUsed: new Date().toISOString() }));

type MockDirNode = { kind: 'dir'; path: string; updatedAt: string };
type MockFileNode = {
  kind: 'file';
  path: string;
  updatedAt: string;
  mimeType: string;
  size: number;
  textContent?: string;
  binaryContent?: Uint8Array;
};
type MockNode = MockDirNode | MockFileNode;
type MockStore = Map<string, MockNode>;

const normalizePath = (rawPath: string): string => rawPath.replace(/^\/+|\/+$/g, '');

const base64ToUint8Array = (base64: string): Uint8Array => {
  if (typeof atob === 'function') {
    return Uint8Array.from(atob(base64), (char) => char.charCodeAt(0));
  }
  const nodeBufferFactory = (globalThis as unknown as { Buffer?: { from(data: string, encoding: string): Uint8Array } }).Buffer;
  if (nodeBufferFactory) {
    return Uint8Array.from(nodeBufferFactory.from(base64, 'base64'));
  }
  throw new Error('No base64 decoder available');
};

const ensureDirectory = (store: MockStore, path: string, updatedAt?: string): MockDirNode => {
  const normalized = normalizePath(path);
  const iso = updatedAt ?? new Date().toISOString();
  const existing = store.get(normalized);
  if (existing && existing.kind === 'dir') {
    existing.updatedAt = iso;
    return existing;
  }
  const node: MockDirNode = { kind: 'dir', path: normalized, updatedAt: iso };
  store.set(normalized, node);
  if (normalized !== '') {
    const parent = normalized.split('/').slice(0, -1).join('/');
    ensureDirectory(store, parent, updatedAt);
  }
  return node;
};

const registerFile = (
  store: MockStore,
  path: string,
  options: { mimeType: string; updatedAt?: string; textContent?: string; binaryContent?: Uint8Array; size?: number },
): MockFileNode => {
  const normalized = normalizePath(path);
  const iso = options.updatedAt ?? new Date().toISOString();
  const parent = normalized.split('/').slice(0, -1).join('/');
  ensureDirectory(store, parent, iso);
  const sizeFromContent = options.textContent
    ? new TextEncoder().encode(options.textContent).length
    : options.binaryContent?.byteLength ?? 0;
  const node: MockFileNode = {
    kind: 'file',
    path: normalized,
    updatedAt: iso,
    mimeType: options.mimeType,
    size: options.size ?? sizeFromContent,
    textContent: options.textContent,
    binaryContent: options.binaryContent,
  };
  store.set(normalized, node);
  return node;
};

const listDirectoryEntries = (store: MockStore, path: string): MockNode[] => {
  const normalized = normalizePath(path);
  ensureDirectory(store, normalized);
  const prefix = normalized ? `${normalized}/` : '';
  const children = new Map<string, MockNode>();
  for (const node of store.values()) {
    if (node.path === normalized) continue;
    if (!node.path.startsWith(prefix)) continue;
    const remainder = node.path.slice(prefix.length);
    if (!remainder) continue;
    const [segment] = remainder.split('/');
    const childPath = normalizePath(prefix + segment);
    if (!children.has(childPath)) {
      const childNode = store.get(childPath);
      if (childNode) children.set(childPath, childNode);
    }
  }
  return Array.from(children.values()).sort((a, b) => {
    const aDir = a.kind === 'dir';
    const bDir = b.kind === 'dir';
    if (aDir !== bDir) return aDir ? -1 : 1;
    const aName = a.path.split('/').pop() ?? a.path;
    const bName = b.path.split('/').pop() ?? b.path;
    return aName.localeCompare(bName);
  });
};

const buildBreadcrumbs = (root: 'media' | 'backup', path: string) => {
  const crumbs: MediaListResponse['breadcrumbs'] = [
    { name: root === 'media' ? 'Media' : 'Backups', path: '' },
  ];
  if (!path) return crumbs;
  const segments = normalizePath(path).split('/');
  let current = '';
  for (const segment of segments) {
    current = current ? `${current}/${segment}` : segment;
    crumbs.push({ name: segment, path: current });
  }
  return crumbs;
};

const getFileNode = (store: MockStore, path: string): MockFileNode | undefined => {
  const node = store.get(normalizePath(path));
  return node && node.kind === 'file' ? node : undefined;
};

const PLACEHOLDER_PNG = base64ToUint8Array(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAAP/XN60AAAAASUVORK5CYII=',
);

const mediaStore: MockStore = new Map();
ensureDirectory(mediaStore, '');
registerFile(mediaStore, 'images/serp_home.png', {
  mimeType: 'image/png',
  binaryContent: PLACEHOLDER_PNG,
  size: PLACEHOLDER_PNG.byteLength,
});
registerFile(mediaStore, 'html/rivercityclean-services.html', {
  mimeType: 'text/html',
  textContent:
    '<html><body><h1>River City Cleaning</h1><p>Updated services overview captured from scraper.</p></body></html>',
});
registerFile(mediaStore, 'reports/weekly-summary.json', {
  mimeType: 'application/json',
  textContent: JSON.stringify({ generatedAt: new Date().toISOString(), totalSnapshots: 18, issuesFound: 3 }, null, 2),
});

const backupStore: MockStore = new Map();
ensureDirectory(backupStore, '');
registerFile(backupStore, 'backup_20240210_0100.tar.gz', {
  mimeType: 'application/gzip',
  binaryContent: new TextEncoder().encode('mock backup archive contents'),
});
registerFile(backupStore, 'backup_20240209_0100.tar.gz', {
  mimeType: 'application/gzip',
  binaryContent: new TextEncoder().encode('older backup archive contents'),
});

const handlers = [
  http.get(`${API_BASE}/dashboard`, async () => {
    await delay(NETWORK_DELAY);
    return HttpResponse.json(dashboard);
  }),
  http.get(`${API_BASE}/targets`, async () => {
    await delay(NETWORK_DELAY);
    return HttpResponse.json(targets);
  }),
  http.post(`${API_BASE}/targets`, async ({ request }) => {
    const payload = (await request.json()) as Partial<Target>;
    const target: Target = {
      id: payload.id ?? createId('tgt'),
      domain: payload.domain ?? 'example.com',
      tags: payload.tags ?? [],
      status: payload.status ?? 'enabled',
      lastScrape: payload.lastScrape ?? null,
      robotsStatus: payload.robotsStatus ?? 'ok',
      nextRun: payload.nextRun ?? new Date().toISOString(),
      depth: payload.depth ?? 2,
      cadence: payload.cadence ?? '0 1 * * *',
      renderBudget: payload.renderBudget ?? 5,
      notes: payload.notes,
    };
    targets = [target, ...targets];
    await delay(NETWORK_DELAY);
    return HttpResponse.json(target, { status: 201 });
  }),
  http.put(`${API_BASE}/targets/:id`, async ({ params, request }) => {
    const id = params.id as string;
    const payload = (await request.json()) as Partial<Target>;
    targets = targets.map((target) => (target.id === id ? { ...target, ...payload } : target));
    const updated = targets.find((target) => target.id === id);
    await delay(NETWORK_DELAY);
    return HttpResponse.json(updated);
  }),
  http.post(`${API_BASE}/targets/:id/run`, async () => {
    await delay(NETWORK_DELAY / 2);
    return new HttpResponse(null, { status: 202 });
  }),
  http.get(`${API_BASE}/schedules`, async () => {
    await delay(NETWORK_DELAY);
    return HttpResponse.json(schedules);
  }),
  http.post(`${API_BASE}/schedules/:id/toggle`, async ({ params, request }) => {
    const id = params.id as string;
    const body = (await request.json()) as { enabled: boolean };
    schedules = schedules.map((schedule) => {
      if (schedule.id !== id) return schedule;
      const nextRun = body.enabled ? new Date(Date.now() + 60 * 60 * 1000).toISOString() : null;
      return {
        ...schedule,
        enabled: body.enabled,
        nextRun,
        lastStatus: body.enabled ? schedule.lastStatus ?? 'queued' : 'disabled',
      };
    });
    const updated = schedules.find((schedule) => schedule.id === id);
    await delay(NETWORK_DELAY);
    return HttpResponse.json(updated);
  }),
  http.post(`${API_BASE}/schedules/:id/run`, async ({ params }) => {
    const id = params.id as string;
    const now = new Date();
    schedules = schedules.map((schedule) => {
      if (schedule.id !== id) return schedule;
      const nextRun = schedule.enabled ? new Date(now.getTime() + 4 * 60 * 60 * 1000).toISOString() : schedule.nextRun ?? null;
      return {
        ...schedule,
        lastRun: now.toISOString(),
        nextRun,
        lastStatus: 'queued',
      };
    });
    const updated = schedules.find((schedule) => schedule.id === id);
    await delay(NETWORK_DELAY / 2);
    if (!updated) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(updated);
  }),
  http.get(`${API_BASE}/status`, async () => {
    await delay(NETWORK_DELAY / 2);
    return HttpResponse.json(refreshSystemStatus());
  }),
  http.get(`${API_BASE}/logs/app`, async ({ request }) => {
    const url = new URL(request.url);
    const lines = Number(url.searchParams.get('lines') ?? '200');
    const trimmed = appLogTail.lines.slice(-lines);
    appLogTail = { ...appLogTail, lines: trimmed, generatedAt: new Date().toISOString() };
    await delay(NETWORK_DELAY / 2);
    return HttpResponse.json(appLogTail);
  }),
  http.get(`${API_BASE}/logs/tasks`, async ({ request }) => {
    const url = new URL(request.url);
    const lines = Number(url.searchParams.get('lines') ?? '200');
    const trimmed = taskLogTail.lines.slice(-lines);
    taskLogTail = { ...taskLogTail, lines: trimmed, generatedAt: new Date().toISOString() };
    await delay(NETWORK_DELAY / 2);
    return HttpResponse.json(taskLogTail);
  }),
  http.get(`${API_BASE}/alerts`, async () => {
    await delay(NETWORK_DELAY / 2);
    return HttpResponse.json(activeAlerts);
  }),
  http.post(`${API_BASE}/alerts/:id/acknowledge`, async ({ params }) => {
    const id = params.id as string;
    activeAlerts = activeAlerts.filter((alert) => alert.id !== id);
    await delay(NETWORK_DELAY / 2);
    return new HttpResponse(null, { status: 204 });
  }),
  http.get(`${API_BASE}/jobs`, async ({ request }) => {
    const url = new URL(request.url);
    const status = (url.searchParams.get('status') as JobStatus) ?? 'running';
    const items = jobStore[status] ?? [];
    await delay(NETWORK_DELAY);
    return HttpResponse.json({ items } satisfies PaginatedJobsResponse);
  }),
  http.get(`${API_BASE}/jobs/:id`, async ({ params }) => {
    const id = params.id as string;
    const job = Object.values(jobStore).flat().find((item) => item.id === id);
    if (!job) {
      return new HttpResponse(null, { status: 404 });
    }
    await delay(NETWORK_DELAY);
    return HttpResponse.json(job);
  }),
  http.post(`${API_BASE}/jobs/:id/retry`, async () => {
    await delay(NETWORK_DELAY / 2);
    return new HttpResponse(null, { status: 202 });
  }),
  http.post(`${API_BASE}/jobs/:id/cancel`, async () => {
    await delay(NETWORK_DELAY / 2);
    return new HttpResponse(null, { status: 202 });
  }),
  http.get(`${API_BASE}/config`, async () => {
    await delay(NETWORK_DELAY);
    return HttpResponse.json(config);
  }),
  http.put(`${API_BASE}/config`, async ({ request }) => {
    const payload = (await request.json()) as ConfigPayload;
    config = payload;
    proxies = payload.proxies;
    userAgents = payload.userAgents.map((value) => ({ id: createId('ua'), value, lastUsed: new Date().toISOString() }));
    await delay(NETWORK_DELAY);
    return HttpResponse.json(config);
  }),
  http.get(`${API_BASE}/logs`, async ({ request }) => {
    const url = new URL(request.url);
    const level = url.searchParams.get('level');
    const domain = url.searchParams.get('domain');
    const jobId = url.searchParams.get('jobId');
    const reasonCode = url.searchParams.get('reasonCode');
    let filtered = logs;
    if (level) filtered = filtered.filter((line) => line.level === level);
    if (domain) filtered = filtered.filter((line) => line.domain === domain);
    if (jobId) filtered = filtered.filter((line) => line.jobId === jobId);
    if (reasonCode) filtered = filtered.filter((line) => line.reasonCode === reasonCode);
    await delay(NETWORK_DELAY);
    return HttpResponse.json({ items: filtered });
  }),
  http.get(`${API_BASE}/snapshots`, async ({ request }) => {
    const url = new URL(request.url);
    const domain = url.searchParams.get('domain');
    const summaries: SnapshotSummary[] = snapshotDetails
      .filter((snapshot) => (domain ? snapshot.domain === domain : true))
      .map(({ html, ...rest }) => ({ ...rest }));
    await delay(NETWORK_DELAY);
    return HttpResponse.json(summaries);
  }),
  http.get(`${API_BASE}/snapshots/:id`, async ({ params }) => {
    const snapshot = snapshotDetails.find((item) => item.id === params.id);
    if (!snapshot) return new HttpResponse(null, { status: 404 });
    await delay(NETWORK_DELAY);
    return HttpResponse.json(snapshot);
  }),
  http.get(`${API_BASE}/snapshots/diff`, async ({ request }) => {
    const url = new URL(request.url);
    const a = snapshotDetails.find((item) => item.id === url.searchParams.get('a'));
    const b = snapshotDetails.find((item) => item.id === url.searchParams.get('b'));
    if (!a || !b) return new HttpResponse(null, { status: 404 });
    await delay(NETWORK_DELAY);
    return HttpResponse.json({ a, b, diff: '' });
  }),
  http.get(`${API_BASE}/quarantine`, async () => {
    await delay(NETWORK_DELAY);
    return HttpResponse.json(quarantine);
  }),
  http.post(`${API_BASE}/quarantine/:domain/release`, async ({ params }) => {
    const domain = decodeURIComponent(params.domain as string);
    quarantine = quarantine.filter((entry) => entry.domain !== domain);
    await delay(NETWORK_DELAY / 2);
    return new HttpResponse(null, { status: 204 });
  }),
  http.post(`${API_BASE}/quarantine/:domain/extend`, async ({ params }) => {
    const domain = decodeURIComponent(params.domain as string);
    quarantine = quarantine.map((entry) =>
      entry.domain === domain
        ? { ...entry, until: new Date(new Date(entry.until).getTime() + 3600000).toISOString() }
        : entry,
    );
    await delay(NETWORK_DELAY / 2);
    return new HttpResponse(null, { status: 202 });
  }),
  http.get(`${API_BASE}/proxies`, async () => {
    await delay(NETWORK_DELAY);
    return HttpResponse.json(proxies);
  }),
  http.put(`${API_BASE}/proxies`, async ({ request }) => {
    const body = (await request.json()) as { proxies: ProxyEntry[] };
    proxies = body.proxies.map((proxy) => ({ ...proxy, id: proxy.id ?? createId('pxy') }));
    config = { ...config, proxies };
    await delay(NETWORK_DELAY);
    return HttpResponse.json(proxies);
  }),
  http.get(`${API_BASE}/user-agents`, async () => {
    await delay(NETWORK_DELAY);
    return HttpResponse.json(userAgents);
  }),
  http.put(`${API_BASE}/user-agents`, async ({ request }) => {
    const body = (await request.json()) as { userAgents: UserAgentEntry[] };
    userAgents = body.userAgents.map((ua) => ({ ...ua, id: ua.id ?? createId('ua') }));
    config = { ...config, userAgents: userAgents.map((ua) => ua.value) };
    await delay(NETWORK_DELAY);
    return HttpResponse.json(userAgents);
  }),
  http.get(`${API_BASE}/media/list`, async ({ request }) => {
    const url = new URL(request.url);
    const root = (url.searchParams.get('root') === 'backup' ? 'backup' : 'media') as 'media' | 'backup';
    const relativePath = normalizePath(url.searchParams.get('path') ?? '');
    const store = root === 'media' ? mediaStore : backupStore;
    const directory = store.get(relativePath);
    if (!directory || directory.kind !== 'dir') {
      await delay(NETWORK_DELAY / 2);
      return new HttpResponse(null, { status: 404 });
    }
    const entries = listDirectoryEntries(store, relativePath).map((node) => ({
      name: node.path.split('/').pop() ?? '',
      path: node.path,
      is_dir: node.kind === 'dir',
      size: node.kind === 'dir' ? 0 : node.size,
      modified_at: node.updatedAt,
      mime_type: node.kind === 'dir' ? null : node.mimeType,
    }));
    const payload: MediaListResponse = {
      root,
      path: relativePath,
      breadcrumbs: buildBreadcrumbs(root, relativePath),
      entries,
    };
    await delay(NETWORK_DELAY / 2);
    return HttpResponse.json(payload);
  }),
  http.get(`${API_BASE}/media/file/:filePath*`, async ({ params, request }) => {
    const url = new URL(request.url);
    const root = (url.searchParams.get('root') === 'backup' ? 'backup' : 'media') as 'media' | 'backup';
    const store = root === 'media' ? mediaStore : backupStore;
    const filePath = normalizePath((params.filePath as string) ?? '');
    const file = getFileNode(store, filePath);
    if (!file) {
      await delay(NETWORK_DELAY / 2);
      return new HttpResponse(null, { status: 404 });
    }
    await delay(NETWORK_DELAY / 2);
    const headers = {
      'Content-Type': file.mimeType,
      'Content-Disposition': `attachment; filename="${encodeURIComponent(file.path.split('/').pop() ?? 'file')}"`,
    };
    if (file.textContent !== undefined) {
      return HttpResponse.text(file.textContent, { status: 200, headers });
    }
    const binary = file.binaryContent ?? new Uint8Array();
    const buffer = binary.buffer.slice(binary.byteOffset, binary.byteOffset + binary.byteLength);
    return HttpResponse.arrayBuffer(buffer, { status: 200, headers });
  }),
];

export { handlers };
