import { http, HttpResponse, delay } from 'msw';
import type {
  ConfigPayload,
  DashboardResponse,
  Job,
  JobStatus,
  LogLine,
  PaginatedJobsResponse,
  ProxyEntry,
  QuarantineEntry,
  Schedule,
  SnapshotDetail,
  SnapshotSummary,
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
  { id: 'CITATIONS_DELTA_DAILY', name: 'Citations Delta Daily', cron: '0 1 * * *', enabled: true, description: 'Checks directories for new NAP changes.' },
  { id: 'BACKLINK_MONITOR_WEEKLY', name: 'Backlink Monitor Weekly', cron: '0 3 * * 1', enabled: true, description: 'Fetches backlink updates for tracked domains.' },
  { id: 'RENDER_CHECK_WEEKLY', name: 'Render Check Weekly', cron: '30 4 * * 1', enabled: false, description: 'Validates JS-required pages still render correctly.' },
  { id: 'SERP_SAMPLER_DAILY', name: 'SERP Sampler Daily', cron: '15 * * * *', enabled: true, description: 'Captures SERP snapshots for key keywords.' },
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
    schedules = schedules.map((schedule) =>
      schedule.id === id ? { ...schedule, enabled: body.enabled } : schedule,
    );
    const updated = schedules.find((schedule) => schedule.id === id);
    await delay(NETWORK_DELAY);
    return HttpResponse.json(updated);
  }),
  http.post(`${API_BASE}/schedules/:id/run`, async () => {
    await delay(NETWORK_DELAY / 2);
    return new HttpResponse(null, { status: 202 });
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
];

export { handlers };
