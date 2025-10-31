import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowDownRight, ArrowUpRight, Activity } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, CartesianGrid, Tooltip as RechartsTooltip, XAxis, YAxis } from 'recharts';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { fetchDashboardSnapshot } from '@/services/api';

export function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboardSnapshot, staleTime: 60_000 });

  const chartData = useMemo(() => {
    if (!data) return [];
    return data.activity
      .slice()
      .reverse()
      .map((item, index) => ({ name: `Day ${index + 1}`, leads: index * 4 + 6 }));
  }, [data]);

  if (isLoading || !data) {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-32 rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {data.metrics.map((metric) => (
          <Card key={metric.label}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{metric.label}</CardTitle>
              {metric.trend === 'up' ? (
                <ArrowUpRight className="h-4 w-4 text-emerald-500" />
              ) : metric.trend === 'down' ? (
                <ArrowDownRight className="h-4 w-4 text-red-500" />
              ) : (
                <Activity className="h-4 w-4 text-muted-foreground" />
              )}
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-semibold">{metric.value}</div>
              <p className="text-xs text-muted-foreground">
                {metric.change > 0 ? '+' : ''}
                {metric.change}% vs. last period
              </p>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Pipeline velocity</CardTitle>
            <CardDescription>Lead progression for the past 14 days</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ left: -20, right: 20 }}>
                <defs>
                  <linearGradient id="colorLead" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--chart-1))" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="hsl(var(--chart-1))" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="name" stroke="currentColor" className="text-xs text-muted-foreground" />
                <YAxis stroke="currentColor" className="text-xs text-muted-foreground" />
                <RechartsTooltip contentStyle={{ background: 'hsl(var(--card))', borderRadius: 8, border: '1px solid hsl(var(--border))' }} />
                <Area type="monotone" dataKey="leads" stroke="hsl(var(--chart-1))" fillOpacity={1} fill="url(#colorLead)" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Platform health</CardTitle>
            <CardDescription>Integration and service statuses</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.health.map((item) => (
              <div key={item.id} className="flex items-start justify-between gap-3 rounded-md border border-border/60 p-3">
                <div>
                  <p className="text-sm font-medium">{item.label}</p>
                  <p className="text-xs text-muted-foreground">{item.detail}</p>
                </div>
                <Badge
                  variant={item.status === 'ok' ? 'secondary' : item.status === 'warning' ? 'outline' : 'destructive'}
                  className={item.status === 'ok' ? 'bg-emerald-500/10 text-emerald-500' : item.status === 'warning' ? 'border-amber-500 text-amber-500' : ''}
                >
                  {item.status.toUpperCase()}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent activity</CardTitle>
            <CardDescription>Workflow updates across the org</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.activity.map((item) => (
                <div key={item.id} className="flex items-start gap-3">
                  <div className="mt-1 h-2.5 w-2.5 rounded-full bg-primary" />
                  <div>
                    <p className="text-sm font-medium">{item.description}</p>
                    <p className="text-xs text-muted-foreground">{new Date(item.timestamp).toLocaleString()}</p>
                  </div>
                  <span className="ml-auto text-xs uppercase text-muted-foreground">{item.actor}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Automation queue</CardTitle>
            <CardDescription>Upcoming AI powered tasks</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <div className="rounded-md border border-dashed p-3">
              <p className="font-medium text-foreground">Change detection</p>
              <p>Next run in 25 minutes.</p>
            </div>
            <div className="rounded-md border border-dashed p-3">
              <p className="font-medium text-foreground">Competitor SERP monitor</p>
              <p>Daily summary scheduled for 7:00 AM.</p>
            </div>
            <div className="rounded-md border border-dashed p-3">
              <p className="font-medium text-foreground">Link audit</p>
              <p>Queued behind 2 jobs.</p>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
