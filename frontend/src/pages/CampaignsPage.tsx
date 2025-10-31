import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Sparkles } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { fetchCampaigns, saveCampaignDraft, type Campaign } from '@/services/api';

const CAMPAIGN_TYPES = ['SEO', 'Email', 'SMS', 'Ads'];

export function CampaignsPage() {
  const queryClient = useQueryClient();
  const { data: campaigns } = useQuery({ queryKey: ['campaigns'], queryFn: fetchCampaigns });
  const [form, setForm] = useState({ name: '', type: 'Email', description: '', scheduleAt: '' });
  const mutation = useMutation({
    mutationFn: () => saveCampaignDraft(form),
    onSuccess: (campaign) => {
      queryClient.setQueryData<Campaign[]>(['campaigns'], (prev) => (prev ? [...prev, campaign] : [campaign]));
      setForm({ name: '', type: 'Email', description: '', scheduleAt: '' });
    }
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Campaign builder</h1>
          <p className="text-sm text-muted-foreground">Design multi-channel campaigns and track their status.</p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" /> Create new campaign
            </CardTitle>
            <CardDescription>Set targeting, choose templates, and schedule outreach.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium">Campaign name</label>
                <Input value={form.name} onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))} />
              </div>
              <div>
                <label className="text-sm font-medium">Type</label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={form.type}
                  onChange={(event) => setForm((prev) => ({ ...prev, type: event.target.value }))}
                >
                  {CAMPAIGN_TYPES.map((type) => (
                    <option key={type}>{type}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Schedule</label>
              <Input type="datetime-local" value={form.scheduleAt} onChange={(event) => setForm((prev) => ({ ...prev, scheduleAt: event.target.value }))} />
            </div>
            <div>
              <label className="text-sm font-medium">Description</label>
              <Textarea rows={4} value={form.description} onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))} />
            </div>
            <div className="rounded-md border border-dashed border-primary/40 bg-primary/5 p-4 text-sm text-primary">
              Tip: Combine SEO audits with automated follow-up sequences to increase conversion.
            </div>
            <div className="flex justify-end">
              <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !form.name}>
                Launch draft
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active campaigns</CardTitle>
            <CardDescription>Monitor progression across channels.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {campaigns?.map((campaign) => (
              <div key={campaign.id} className="rounded-lg border border-border/60 p-3 text-sm">
                <div className="flex items-center justify-between">
                  <p className="font-semibold">{campaign.name}</p>
                  <Badge variant="outline" className="capitalize">
                    {campaign.status}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  {campaign.type} · {new Date(campaign.startDate).toLocaleDateString()}
                </p>
              </div>
            ))}
            {!campaigns?.length && <p className="text-sm text-muted-foreground">No campaigns yet.</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
