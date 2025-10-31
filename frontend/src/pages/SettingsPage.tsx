import { useState } from 'react';
import { useMutation, useQueries, useQueryClient } from '@tanstack/react-query';
import { MailPlus } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { fetchIntegrationSettings, fetchSystemSettings, fetchUsers, inviteUser, updateSystemSetting, type IntegrationSetting, type SystemSetting, type TeamUser } from '@/services/api';

const ROLE_OPTIONS = ['admin', 'manager', 'sales', 'tech', 'service'] as const;

export function SettingsPage() {
  const queryClient = useQueryClient();
  const results = useQueries({
    queries: [
      { queryKey: ['users'], queryFn: fetchUsers },
      { queryKey: ['integrations'], queryFn: fetchIntegrationSettings },
      { queryKey: ['system-settings'], queryFn: fetchSystemSettings }
    ]
  });

  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<typeof ROLE_OPTIONS[number]>('sales');

  const inviteMutation = useMutation({
    mutationFn: () => inviteUser(inviteEmail, inviteRole),
    onSuccess: (user) => {
      queryClient.setQueryData<TeamUser[]>(['users'], (prev) => (prev ? [...prev, user] : [user]));
      setInviteEmail('');
    }
  });

  const settingMutation = useMutation({
    mutationFn: ({ id, value }: { id: string; value: SystemSetting['value'] }) => updateSystemSetting(id, value),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['system-settings'] })
  });

  const [users, integrations, systemSettings] = results.map((result) => result.data) as [TeamUser[] | undefined, IntegrationSetting[] | undefined, SystemSetting[] | undefined];

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">Manage users, integrations, and system preferences.</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>User management</CardTitle>
            <CardDescription>Invite teammates and manage roles.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-[2fr_1fr_1fr]">
              <Input
                placeholder="name@example.com"
                value={inviteEmail}
                onChange={(event) => setInviteEmail(event.target.value)}
                type="email"
              />
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={inviteRole}
                onChange={(event) => setInviteRole(event.target.value as typeof ROLE_OPTIONS[number])}
              >
                {ROLE_OPTIONS.map((role) => (
                  <option key={role}>{role}</option>
                ))}
              </select>
              <Button onClick={() => inviteMutation.mutate()} disabled={inviteMutation.isPending || !inviteEmail}>
                <MailPlus className="mr-2 h-4 w-4" /> Invite
              </Button>
            </div>
            <div className="space-y-3">
              {users?.map((user) => (
                <div key={user.id} className="flex items-center justify-between rounded-md border border-border/60 p-3 text-sm">
                  <div>
                    <p className="font-medium">{user.name}</p>
                    <p className="text-xs text-muted-foreground">{user.email}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="capitalize">
                      {user.role}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      Active {user.lastActiveAt ? new Date(user.lastActiveAt).toLocaleString() : 'unknown'}
                    </span>
                  </div>
                </div>
              ))}
              {!users?.length && <p className="text-sm text-muted-foreground">No users loaded.</p>}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Integrations</CardTitle>
            <CardDescription>Connect third-party services for automations.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {integrations?.map((integration) => (
              <div key={integration.id} className="rounded-lg border border-border/60 p-3 text-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold">{integration.name}</p>
                    <p className="text-xs text-muted-foreground">{integration.description}</p>
                  </div>
                  <Badge className={integration.status === 'connected' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'}>
                    {integration.status}
                  </Badge>
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Last checked {new Date(integration.lastCheckedAt).toLocaleString()}
                </p>
              </div>
            ))}
            {!integrations?.length && <p className="text-sm text-muted-foreground">No integrations configured.</p>}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>System settings</CardTitle>
          <CardDescription>Control automation parameters and schedules.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {systemSettings?.map((setting) => (
            <div
              key={`${setting.id}-${String(setting.value)}`}
              className="flex flex-col gap-2 rounded-md border border-border/60 p-3 text-sm md:flex-row md:items-center md:justify-between"
            >
              <div>
                <p className="font-medium">{setting.label}</p>
                <p className="text-xs text-muted-foreground">{setting.description}</p>
              </div>
              {typeof setting.value === 'boolean' ? (
                <Switch
                  checked={Boolean(setting.value)}
                  onCheckedChange={(checked) => settingMutation.mutate({ id: setting.id, value: checked })}
                />
              ) : (
                <Input
                  className="max-w-xs"
                  defaultValue={String(setting.value)}
                  onBlur={(event) => settingMutation.mutate({ id: setting.id, value: event.target.value })}
                />
              )}
            </div>
          ))}
          {!systemSettings?.length && <p className="text-sm text-muted-foreground">No settings available.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
