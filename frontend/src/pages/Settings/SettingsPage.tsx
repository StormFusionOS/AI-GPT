import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/components/ui/use-toast';
import type { ConfigPayload } from '@/types';

export function SettingsPage() {
  const { data } = useQuery({ queryKey: ['config'], queryFn: api.getConfig });
  const [alerts, setAlerts] = useState<{ email: string; slack: string }>({ email: '', slack: '' });
  const [retention, setRetention] = useState({ logsDays: 30, snapshotsDays: 90 });
  const [featureFlags, setFeatureFlags] = useState<Record<string, boolean>>({});
  const { toast } = useToast();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (data) {
      setAlerts({ email: data.alerts.email.join(', '), slack: data.alerts.slackWebhooks.join(', ') });
      setRetention(data.retention);
      setFeatureFlags(data.featureFlags);
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: (payload: Partial<ConfigPayload>) => api.saveConfig({ ...data!, ...payload }),
    onSuccess: (response) => {
      queryClient.setQueryData(['config'], response);
      toast({ title: 'Settings saved' });
    },
    onError: () => toast({ title: 'Failed to save settings', variant: 'destructive' }),
  });

  function handleSave() {
    if (!data) return;
    const updated: ConfigPayload = {
      ...data,
      alerts: {
        email: alerts.email.split(',').map((value) => value.trim()).filter(Boolean),
        slackWebhooks: alerts.slack.split(',').map((value) => value.trim()).filter(Boolean),
      },
      retention,
      featureFlags,
    };
    saveMutation.mutate(updated);
  }

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle>Alert Channels</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="emailAlerts">Email addresses</Label>
            <Input
              id="emailAlerts"
              value={alerts.email}
              onChange={(event) => setAlerts((prev) => ({ ...prev, email: event.target.value }))}
              placeholder="ops@example.com, dev@example.com"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="slackWebhooks">Slack webhooks</Label>
            <Input
              id="slackWebhooks"
              value={alerts.slack}
              onChange={(event) => setAlerts((prev) => ({ ...prev, slack: event.target.value }))}
              placeholder="https://hooks.slack.com/..."
            />
          </div>
        </CardContent>
      </Card>
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle>Retention</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="logsDays">Log retention (days)</Label>
            <Input
              id="logsDays"
              type="number"
              min={1}
              value={retention.logsDays}
              onChange={(event) => setRetention((prev) => ({ ...prev, logsDays: Number(event.target.value) }))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="snapshotsDays">Snapshot retention (days)</Label>
            <Input
              id="snapshotsDays"
              type="number"
              min={1}
              value={retention.snapshotsDays}
              onChange={(event) => setRetention((prev) => ({ ...prev, snapshotsDays: Number(event.target.value) }))}
            />
          </div>
        </CardContent>
      </Card>
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle>Feature Flags</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {Object.keys(featureFlags).length === 0 && (
            <p className="text-sm text-muted-foreground">No feature flags configured.</p>
          )}
          {Object.entries(featureFlags).map(([flag, enabled]) => (
            <div key={flag} className="flex items-center justify-between gap-2">
              <div>
                <p className="text-sm font-medium capitalize">{flag.replace(/_/g, ' ')}</p>
                <p className="text-xs text-muted-foreground">Toggle experimental functionality</p>
              </div>
              <Switch checked={enabled} onCheckedChange={(value) => setFeatureFlags((prev) => ({ ...prev, [flag]: value }))} />
            </div>
          ))}
        </CardContent>
      </Card>
      <div className="lg:col-span-3 flex justify-end">
        <Button onClick={handleSave} disabled={saveMutation.isPending}>
          Save Settings
        </Button>
      </div>
    </div>
  );
}
