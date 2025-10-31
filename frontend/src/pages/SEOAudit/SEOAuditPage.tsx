import { useDeferredValue, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import type { AuditDetail, AuditSummary } from '@/types';
import { formatDate } from '@/lib/utils';

const severityColor: Record<AuditSummary['topSeverity'], string> = {
  low: 'bg-emerald-500/10 text-emerald-600',
  medium: 'bg-amber-500/10 text-amber-600',
  high: 'bg-orange-500/10 text-orange-600',
  critical: 'bg-red-500/10 text-red-600',
};

export function SEOAuditPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<AuditSummary['topSeverity'] | 'all'>('all');
  const [selectedAudit, setSelectedAudit] = useState<AuditSummary | null>(null);

  const deferredSearch = useDeferredValue(searchTerm.trim());

  const { data: audits } = useQuery({
    queryKey: ['seo-audits', { search: deferredSearch, severity: severityFilter }],
    queryFn: () =>
      api.getSeoAudits({
        search: deferredSearch || undefined,
        severity: severityFilter === 'all' ? undefined : severityFilter,
      }),
  });

  const filteredAudits = useMemo(() => audits ?? [], [audits]);

  const { data: auditDetail } = useQuery({
    queryKey: ['seo-audit-detail', selectedAudit?.id],
    queryFn: () => api.getSeoAuditDetail(selectedAudit!.id),
    enabled: Boolean(selectedAudit?.id),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">SEO Audits</h1>
          <p className="text-sm text-muted-foreground">
            Track crawl results, structured data checks, and page-level issues surfaced by the auditing pipeline.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="search"
            placeholder="Search by URL"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <select
            value={severityFilter}
            onChange={(event) => setSeverityFilter(event.target.value as AuditSummary['topSeverity'] | 'all')}
            className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="all">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Audits</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-border text-sm">
              <thead className="bg-muted/50 text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">URL</th>
                  <th className="px-3 py-2 text-left font-medium">Audit Date</th>
                  <th className="px-3 py-2 text-left font-medium">Score</th>
                  <th className="px-3 py-2 text-left font-medium">Open Issues</th>
                  <th className="px-3 py-2 text-left font-medium">Trend</th>
                  <th className="px-3 py-2 text-left font-medium">Severity</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredAudits.map((audit) => (
                  <tr key={audit.id} className="hover:bg-muted/40">
                    <td className="px-3 py-3 text-sm font-medium text-foreground">{audit.url}</td>
                    <td className="px-3 py-3 text-xs text-muted-foreground">{formatDate(audit.auditDate)}</td>
                    <td className="px-3 py-3 text-sm font-semibold">{audit.score}</td>
                    <td className="px-3 py-3 text-sm">{audit.issueCount}</td>
                    <td className="px-3 py-3 text-xs capitalize text-muted-foreground">{audit.trend}</td>
                    <td className="px-3 py-3">
                      <span className={`rounded-full px-2 py-1 text-xs font-semibold ${severityColor[audit.topSeverity]}`}>
                        {audit.topSeverity}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-right">
                      <Button size="sm" variant="outline" onClick={() => setSelectedAudit(audit)}>
                        View
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!filteredAudits.length && (
              <div className="py-12 text-center text-sm text-muted-foreground">No audits match your filters yet.</div>
            )}
          </div>
        </CardContent>
      </Card>

      <Dialog open={Boolean(selectedAudit)} onOpenChange={(open) => !open && setSelectedAudit(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Audit Findings</DialogTitle>
          </DialogHeader>
          {auditDetail ? <AuditDetailView detail={auditDetail} /> : <div className="text-sm">Loading findings…</div>}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function AuditDetailView({ detail }: { detail: AuditDetail }) {
  return (
    <div className="space-y-4">
      <div>
        <p className="font-semibold text-foreground">{detail.url}</p>
        <p className="text-xs text-muted-foreground">Audited {formatDate(detail.auditDate)} · Score {detail.score}</p>
      </div>
      <p className="text-sm text-muted-foreground">{detail.summary}</p>
      <ScrollArea className="h-72 rounded-md border">
        <div className="space-y-3 p-4">
          {detail.issues.map((issue) => (
            <div key={issue.id} className="rounded-md border border-border bg-card p-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold">{issue.description}</h3>
                <Badge variant={issue.resolved ? 'muted' : 'warning'}>{issue.severity}</Badge>
              </div>
              {issue.recommendation && (
                <p className="mt-2 text-xs text-muted-foreground">Recommendation: {issue.recommendation}</p>
              )}
              {issue.resolved && <p className="mt-2 text-xs text-emerald-600">Resolved</p>}
            </div>
          ))}
          {!detail.issues.length && <div className="text-sm text-muted-foreground">No issues detected.</div>}
        </div>
      </ScrollArea>
    </div>
  );
}
