import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { YamlJsonEditor } from '@/components/YamlJsonEditor';
import { useToast } from '@/components/ui/use-toast';
import yaml from 'js-yaml';
import { z } from 'zod';
import type { ConfigPayload } from '@/types';

const configSchema = z.object({
  proxies: z.array(
    z.object({
      id: z.string().optional(),
      host: z.string(),
      port: z.number(),
      username: z.string().optional(),
      password: z.string().optional(),
    }),
  ),
  userAgents: z.array(z.string()),
  rateLimits: z.object({
    globalRpm: z.number().nonnegative(),
    domainConcurrency: z.number().nonnegative(),
  }),
  renderBudget: z.object({ headlessPagesPerHour: z.number().nonnegative() }),
  quarantine: z.object({ retryAfterMinutes: z.number().nonnegative() }),
  featureFlags: z.record(z.boolean()),
  alerts: z.object({
    email: z.array(z.string().email().or(z.string())),
    slackWebhooks: z.array(z.string()),
  }),
  retention: z.object({
    logsDays: z.number().nonnegative(),
    snapshotsDays: z.number().nonnegative(),
  }),
});

export function ConfigPage() {
  const { data, isLoading } = useQuery({ queryKey: ['config'], queryFn: api.getConfig });
  const [rawConfig, setRawConfig] = useState('');
  const [error, setError] = useState<string | undefined>();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (data) {
      setRawConfig(yaml.dump(data));
    }
  }, [data]);

  const parsed = useMemo(() => {
    if (!rawConfig) return { data: undefined as ConfigPayload | undefined, error: undefined };
    try {
      const candidate = yaml.load(rawConfig) as ConfigPayload;
      const result = configSchema.safeParse(candidate);
      if (!result.success) {
        return { data: undefined, error: result.error.errors.map((err) => err.message).join('\n') };
      }
      return { data: result.data, error: undefined };
    } catch (err) {
      return { data: undefined, error: (err as Error).message };
    }
  }, [rawConfig]);

  useEffect(() => {
    setError(parsed.error);
  }, [parsed.error]);

  const parsedConfig = parsed.data;

  const saveMutation = useMutation({
    mutationFn: api.saveConfig,
    onSuccess: (response) => {
      queryClient.setQueryData(['config'], response);
      toast({ title: 'Configuration saved' });
    },
    onError: () => toast({ title: 'Failed to save config', variant: 'destructive' }),
  });

  function handleSave() {
    if (!parsedConfig) {
      toast({ title: 'Resolve validation errors first', variant: 'destructive' });
      return;
    }
    saveMutation.mutate(parsedConfig);
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle>Scraper Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <div className="text-sm text-muted-foreground">Loading configuration…</div>
          ) : (
            <YamlJsonEditor label="YAML Config" value={rawConfig} onChange={setRawConfig} error={error} rows={24} />
          )}
          <Button onClick={handleSave} disabled={saveMutation.isPending || Boolean(error)}>
            Save Config
          </Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Preview</CardTitle>
        </CardHeader>
        <CardContent>
          {parsedConfig ? (
            <pre className="max-h-[600px] overflow-auto rounded bg-muted p-4 text-xs">
              {JSON.stringify(parsedConfig, null, 2)}
            </pre>
          ) : (
            <p className="text-sm text-muted-foreground">Fix validation errors to view JSON preview.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
