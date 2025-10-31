import { Outlet } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Sidebar } from '@/components/layout/Sidebar';
import { Topbar } from '@/components/layout/Topbar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { api } from '@/services/api';
import type { AlertItem } from '@/types';

function AlertsStrip() {
  const queryClient = useQueryClient();
  const { data: alerts = [] } = useQuery({
    queryKey: ['alerts'],
    queryFn: api.getAlerts,
    refetchInterval: 60_000,
  });

  const acknowledgeMutation = useMutation({
    mutationFn: api.acknowledgeAlert,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  });

  if (alerts.length === 0) {
    return null;
  }

  function variantFor(alert: AlertItem) {
    if (alert.severity === 'critical') return 'destructive' as const;
    if (alert.severity === 'warning') return 'warning' as const;
    return 'secondary' as const;
  }

  return (
    <div className="border-b border-border bg-destructive/10">
      <div className="space-y-2 px-4 py-3">
        {alerts.map((alert) => (
          <div key={alert.id} className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-1 items-center gap-2">
              <Badge variant={variantFor(alert)} className="uppercase">
                {alert.severity}
              </Badge>
              <span className="text-sm font-medium text-destructive">{alert.message}</span>
            </div>
            <Button
              size="xs"
              variant="outline"
              onClick={() => acknowledgeMutation.mutate(alert.id)}
              disabled={acknowledgeMutation.isLoading}
            >
              Dismiss
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}

export function DashboardLayout() {
  return (
    <div className="flex h-screen w-full bg-background text-foreground">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Topbar />
        <AlertsStrip />
        <main className="flex-1 overflow-y-auto bg-background p-4">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
