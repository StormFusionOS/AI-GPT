import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';

export function SchedulesPage() {
  const { data = [], isLoading } = useQuery({ queryKey: ['schedules'], queryFn: api.getSchedules });
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) => api.toggleSchedule(id, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['schedules'] }),
  });

  const runMutation = useMutation({
    mutationFn: api.runScheduleNow,
    onSuccess: () => {
      toast({ title: 'Schedule dispatched' });
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
    },
  });

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading schedules…</div>;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {data.map((schedule) => (
        <Card key={schedule.id}>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">{schedule.name}</CardTitle>
            <Switch
              checked={schedule.enabled}
              onCheckedChange={(value) =>
                toggleMutation.mutate({ id: schedule.id, enabled: value }, {
                  onError: () => toast({ title: 'Failed to update schedule', variant: 'destructive' }),
                })
              }
              aria-label={`Toggle ${schedule.name}`}
            />
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <div>
              <span className="font-semibold text-foreground">Cron:</span> {schedule.cron}
            </div>
            {schedule.nextRun && (
              <div>
                <span className="font-semibold text-foreground">Next run:</span> {new Date(schedule.nextRun).toLocaleString()}
              </div>
            )}
            {schedule.lastRun && (
              <div>
                <span className="font-semibold text-foreground">Last run:</span> {new Date(schedule.lastRun).toLocaleString()}
              </div>
            )}
            {schedule.lastStatus && (
              <div>
                <span className="font-semibold text-foreground">Last status:</span> {schedule.lastStatus}
              </div>
            )}
            {schedule.description && <p>{schedule.description}</p>}
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                runMutation.mutate(schedule.id, {
                  onError: () => toast({ title: 'Failed to run schedule', variant: 'destructive' }),
                })
              }
            >
              Run Now
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
