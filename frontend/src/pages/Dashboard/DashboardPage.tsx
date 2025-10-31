import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { KpiCard } from '@/components/KpiCard';
import { DomainHealthCard } from '@/components/DomainHealthCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { JobStatusBadge } from '@/components/JobStatusBadge';
import { formatDate } from '@/lib/utils';
import { useToast } from '@/components/ui/use-toast';
import { PromptRunnerModal } from '@/components/PromptRunnerModal';

export function DashboardPage() {
  const [promptRunnerOpen, setPromptRunnerOpen] = useState(false);
  const { data, isLoading, isError } = useQuery({ queryKey: ['dashboard'], queryFn: api.getDashboard });
  const { toast } = useToast();

  if (isLoading) {
    return <div className="animate-pulse text-sm text-muted-foreground">Loading dashboard…</div>;
  }

  if (isError || !data) {
    return <div className="text-sm text-destructive">Failed to load dashboard data.</div>;
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Tracked Domains" value={data.trackedDomains} description="Domains monitored across all job types" />
        <KpiCard label="Active Jobs" value={data.activeJobs} description="Currently executing across workers" />
        <KpiCard label="Last Run Status" value={data.lastRunStatus.toUpperCase()} />
        <KpiCard label="Queue Depth" value={data.queueDepth} description="Pending jobs waiting to be assigned" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Recent Events</CardTitle>
            <Button
              variant="outline"
              size="sm"
              disabled
              onClick={() =>
                toast({
                  title: 'Not yet wired',
                  description: 'Backend actions will be enabled once the API is connected.',
                })
              }
            >
              Run All Targets
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.recentEvents.map((event) => (
                <div key={event.id} className="flex items-center justify-between rounded-md border border-border p-3">
                  <div>
                    <div className="font-medium">{event.domain}</div>
                    <div className="text-xs text-muted-foreground">{event.jobType}</div>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <JobStatusBadge status={event.status} />
                    <span className="text-xs text-muted-foreground">{formatDate(event.occurredAt)}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button className="w-full" disabled>
              Run All Targets
            </Button>
            <Button className="w-full" variant="outline" disabled>
              Drain Queue
            </Button>
            <Button className="w-full" variant="outline" disabled>
              Pause Crawlers
            </Button>
            <Button className="w-full" variant="secondary" onClick={() => setPromptRunnerOpen(true)}>
              Launch Prompt Runner
            </Button>
          </CardContent>
        </Card>
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold">Domain Health</h2>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {data.domainHealth.map((item) => (
            <DomainHealthCard key={item.domain} {...item} />
          ))}
        </div>
      </div>

      <PromptRunnerModal open={promptRunnerOpen} onOpenChange={setPromptRunnerOpen} />
    </div>
  );
}
