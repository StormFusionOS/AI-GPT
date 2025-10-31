import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { formatDate, formatRelativeTime } from '@/lib/utils';

function statusVariant(status: 'ok' | 'warn' | 'error') {
  switch (status) {
    case 'ok':
      return 'default';
    case 'warn':
      return 'warning';
    case 'error':
    default:
      return 'destructive';
  }
}

export function SystemStatusPage() {
  const [autoRefresh, setAutoRefresh] = useState(true);

  const statusQuery = useQuery({
    queryKey: ['system-status'],
    queryFn: api.getSystemStatus,
    refetchInterval: autoRefresh ? 60_000 : false,
  });

  const appLogQuery = useQuery({
    queryKey: ['log-tail', 'app', autoRefresh],
    queryFn: () => api.getAppLogTail(200),
    refetchInterval: autoRefresh ? 60_000 : false,
  });

  const taskLogQuery = useQuery({
    queryKey: ['log-tail', 'tasks', autoRefresh],
    queryFn: () => api.getTaskLogTail(200),
    refetchInterval: autoRefresh ? 60_000 : false,
  });

  const status = statusQuery.data;
  const integrity = status?.integrityFindings ?? [];
  const wordpress = status?.wordpress ?? [];

  const logTabs = useMemo(
    () => [
      {
        id: 'app',
        label: 'Application',
        lines: appLogQuery.data?.lines ?? [],
        updatedAt: appLogQuery.data?.generatedAt ?? null,
      },
      {
        id: 'tasks',
        label: 'Tasks',
        lines: taskLogQuery.data?.lines ?? [],
        updatedAt: taskLogQuery.data?.generatedAt ?? null,
      },
    ],
    [appLogQuery.data, taskLogQuery.data],
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">System Status</h1>
          <p className="text-sm text-muted-foreground">Operational overview, alerts, and recent log output.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Switch id="auto-refresh" checked={autoRefresh} onCheckedChange={setAutoRefresh} />
            <label htmlFor="auto-refresh">Auto refresh</label>
          </div>
          <Button variant="outline" onClick={() => statusQuery.refetch()} disabled={statusQuery.isFetching}>
            Refresh now
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">CPU Usage</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {status ? `${status.resourceUsage.cpuPercent.toFixed(1)}%` : '—'}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Memory Usage</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {status ? `${status.resourceUsage.memoryPercent.toFixed(1)}%` : '—'}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Disk Usage</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {status ? `${status.resourceUsage.diskPercent.toFixed(1)}%` : '—'}
            <div className="text-xs font-normal text-muted-foreground">
              Free: {status ? Math.round(status.resourceUsage.diskFreeBytes / (1024 * 1024 * 1024)) : '—'} GB
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Last Backup</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            <div className="text-base font-semibold text-foreground">
              {status?.lastBackupAt ? formatRelativeTime(status.lastBackupAt) : 'No backup found'}
            </div>
            <div className="text-muted-foreground">{formatDate(status?.lastBackupAt ?? null)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Last Scraper Run</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            <div className="text-base font-semibold text-foreground">
              {status?.lastScraperRunAt ? formatRelativeTime(status.lastScraperRunAt) : 'No runs recorded'}
            </div>
            <div className="text-muted-foreground">{formatDate(status?.lastScraperRunAt ?? null)}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <CardTitle>Component Health</CardTitle>
          <div className="text-xs text-muted-foreground">
            Last updated {formatRelativeTime(status?.generatedAt ?? null)}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {(status?.checks ?? []).map((check) => (
              <div key={check.id} className="rounded-md border border-border p-3">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{check.name}</span>
                  <Badge variant={statusVariant(check.status)} className="capitalize">
                    {check.status}
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{check.message}</p>
                {check.value && <p className="mt-1 text-xs text-muted-foreground">Value: {check.value}</p>}
              </div>
            ))}
            {statusQuery.isLoading && <div className="text-sm text-muted-foreground">Loading checks…</div>}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>File Integrity</CardTitle>
          </CardHeader>
          <CardContent>
            {integrity.length === 0 && <p className="text-sm text-muted-foreground">No integrity deviations detected.</p>}
            {integrity.length > 0 && (
              <ScrollArea className="max-h-60">
                <div className="space-y-3 pr-2 text-sm">
                  {integrity.map((finding) => (
                    <div key={`${finding.path}-${finding.observedAt}`} className="rounded-md border border-border p-3">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold">{finding.status}</span>
                        <span className="text-xs text-muted-foreground">{formatRelativeTime(finding.observedAt)}</span>
                      </div>
                      <div className="font-mono text-xs text-muted-foreground">{finding.path}</div>
                      <div className="text-sm text-muted-foreground">{finding.message}</div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>WordPress Plugin Audits</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {wordpress.length === 0 && <p className="text-sm text-muted-foreground">No WordPress sites configured.</p>}
            {wordpress.map((site) => (
              <div key={site.baseUrl} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold">{site.site}</div>
                    <div className="text-xs text-muted-foreground">{site.baseUrl}</div>
                  </div>
                  <div className="text-xs text-muted-foreground">Checked {formatRelativeTime(site.checkedAt)}</div>
                </div>
                <div className="space-y-2">
                  {site.plugins.map((plugin) => (
                    <div key={`${site.baseUrl}-${plugin.slug}`} className="rounded-md border border-border p-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">{plugin.name}</span>
                        <Badge
                          variant={plugin.severity === 'critical' ? 'destructive' : plugin.severity === 'warning' ? 'warning' : 'secondary'}
                          className="capitalize"
                        >
                          {plugin.status}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Installed {plugin.installedVersion}
                        {plugin.latestVersion ? ` · Latest ${plugin.latestVersion}` : ''}
                      </div>
                      {plugin.notes && <div className="text-xs text-muted-foreground">{plugin.notes}</div>}
                    </div>
                  ))}
                  {site.errors.map((error) => (
                    <div key={`${site.baseUrl}-error-${error}`} className="rounded-md border border-destructive/50 bg-destructive/5 p-2 text-xs text-destructive">
                      {error}
                    </div>
                  ))}
                </div>
                <Separator />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>Log Tail</CardTitle>
            {status && (
              <div className="mt-1 text-xs text-muted-foreground">
                App alerts: {status.logSummary.appErrors} · Task alerts: {status.logSummary.taskErrors}
              </div>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              appLogQuery.refetch();
              taskLogQuery.refetch();
            }}
          >
            Refresh logs
          </Button>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="app">
            <TabsList>
              {logTabs.map((tab) => (
                <TabsTrigger key={tab.id} value={tab.id} className="capitalize">
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>
            {logTabs.map((tab) => (
              <TabsContent key={tab.id} value={tab.id} className="mt-4">
                <div className="mb-2 text-xs text-muted-foreground">
                  Updated {formatRelativeTime(tab.updatedAt)}
                </div>
                <ScrollArea className="h-64 rounded-md border border-border bg-muted/30">
                  <pre className="whitespace-pre-wrap p-3 text-xs font-mono leading-relaxed">
                    {tab.lines.length > 0 ? tab.lines.join('\n') : 'No log lines available.'}
                  </pre>
                </ScrollArea>
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
