import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { ProxyEntry, UserAgentEntry } from '@/types';
import { useToast } from '@/components/ui/use-toast';

export function ProxiesPage() {
  const proxiesQuery = useQuery({ queryKey: ['proxies'], queryFn: api.getProxies });
  const userAgentsQuery = useQuery({ queryKey: ['userAgents'], queryFn: api.getUserAgents });
  const [proxies, setProxies] = useState<ProxyEntry[]>([]);
  const [userAgents, setUserAgents] = useState<UserAgentEntry[]>([]);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (proxiesQuery.data) setProxies(proxiesQuery.data);
  }, [proxiesQuery.data]);

  useEffect(() => {
    if (userAgentsQuery.data) setUserAgents(userAgentsQuery.data);
  }, [userAgentsQuery.data]);

  const saveProxiesMutation = useMutation({
    mutationFn: api.saveProxies,
    onSuccess: (response) => {
      setProxies(response);
      queryClient.setQueryData(['proxies'], response);
      toast({ title: 'Proxy pool saved' });
    },
    onError: () => toast({ title: 'Failed to save proxies', variant: 'destructive' }),
  });

  const saveUserAgentsMutation = useMutation({
    mutationFn: api.saveUserAgents,
    onSuccess: (response) => {
      setUserAgents(response);
      queryClient.setQueryData(['userAgents'], response);
      toast({ title: 'User agents saved' });
    },
    onError: () => toast({ title: 'Failed to save user agents', variant: 'destructive' }),
  });

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader className="flex items-center justify-between">
          <CardTitle>Proxies</CardTitle>
          <Button
            size="sm"
            onClick={() =>
              setProxies((prev) => [
                ...prev,
                {
                  id:
                    typeof crypto !== 'undefined' && 'randomUUID' in crypto
                      ? crypto.randomUUID()
                      : `pxy-${Date.now()}`,
                  host: '',
                  port: 3128,
                  username: '',
                  password: '',
                  lastHealthCheck: undefined,
                },
              ])
            }
          >
            Add Proxy
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {proxies.map((proxy, index) => (
            <div key={proxy.id} className="grid gap-2 rounded border border-border p-3 md:grid-cols-5">
              <Input
                value={proxy.host}
                placeholder="Host"
                onChange={(event) =>
                  setProxies((prev) => prev.map((item, i) => (i === index ? { ...item, host: event.target.value } : item)))
                }
              />
              <Input
                type="number"
                value={proxy.port}
                placeholder="Port"
                onChange={(event) =>
                  setProxies((prev) => prev.map((item, i) => (i === index ? { ...item, port: Number(event.target.value) } : item)))
                }
              />
              <Input
                value={proxy.username ?? ''}
                placeholder="Username"
                onChange={(event) =>
                  setProxies((prev) => prev.map((item, i) => (i === index ? { ...item, username: event.target.value } : item)))
                }
              />
              <Input
                value={proxy.password ?? ''}
                placeholder="Password"
                type="password"
                onChange={(event) =>
                  setProxies((prev) => prev.map((item, i) => (i === index ? { ...item, password: event.target.value } : item)))
                }
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => setProxies((prev) => prev.filter((_, i) => i !== index))}
              >
                Remove
              </Button>
            </div>
          ))}
          <Button onClick={() => saveProxiesMutation.mutate(proxies)} disabled={saveProxiesMutation.isPending}>
            Save Proxies
          </Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex items-center justify-between">
          <CardTitle>User Agents</CardTitle>
          <Button
            size="sm"
            onClick={() =>
              setUserAgents((prev) => [
                ...prev,
                {
                  id:
                    typeof crypto !== 'undefined' && 'randomUUID' in crypto
                      ? crypto.randomUUID()
                      : `ua-${Date.now()}`,
                  value: '',
                  lastUsed: undefined,
                },
              ])
            }
          >
            Add User Agent
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {userAgents.map((ua, index) => (
            <div key={ua.id} className="flex gap-2">
              <Input
                value={ua.value}
                placeholder="Mozilla/5.0 ..."
                onChange={(event) =>
                  setUserAgents((prev) => prev.map((item, i) => (i === index ? { ...item, value: event.target.value } : item)))
                }
              />
              <Button variant="outline" onClick={() => setUserAgents((prev) => prev.filter((_, i) => i !== index))}>
                Remove
              </Button>
            </div>
          ))}
          <Button onClick={() => saveUserAgentsMutation.mutate(userAgents)} disabled={saveUserAgentsMutation.isPending}>
            Save User Agents
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
