import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';
import { useToast } from '@/components/ui/use-toast';

const LEVEL_OPTIONS = ['ALL', 'INFO', 'WARN', 'ERROR'] as const;

type Level = (typeof LEVEL_OPTIONS)[number];

export function LogsPage() {
  const [level, setLevel] = useState<Level>('ALL');
  const [domain, setDomain] = useState('');
  const [jobId, setJobId] = useState('');
  const [reasonCode, setReasonCode] = useState('');
  const { toast } = useToast();

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['logs', level, domain, jobId, reasonCode],
    queryFn: () =>
      api.getLogs({
        level: level === 'ALL' ? undefined : level,
        domain: domain || undefined,
        jobId: jobId || undefined,
        reasonCode: reasonCode || undefined,
      }),
    refetchInterval: 5000,
  });

  const logLines = useMemo(() => data?.items ?? [], [data]);

  function handleCopy() {
    const text = logLines.map((line) => `${line.timestamp} [${line.level}] ${line.message}`).join('\n');
    navigator.clipboard.writeText(text).then(() => toast({ title: 'Logs copied' }));
  }

  function handleDownload() {
    const text = logLines.map((line) => JSON.stringify(line)).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `logs-${Date.now()}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase text-muted-foreground">Level</label>
          <select
            value={level}
            onChange={(event) => setLevel(event.target.value as Level)}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            {LEVEL_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase text-muted-foreground">Domain</label>
          <Input value={domain} onChange={(event) => setDomain(event.target.value)} placeholder="domain.com" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase text-muted-foreground">Job ID</label>
          <Input value={jobId} onChange={(event) => setJobId(event.target.value)} placeholder="job-uuid" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase text-muted-foreground">Reason Code</label>
          <Input value={reasonCode} onChange={(event) => setReasonCode(event.target.value)} placeholder="RATE_LIMIT_429" />
        </div>
        <Button onClick={() => refetch()} disabled={isRefetching} variant="outline">
          Refresh
        </Button>
        <Button onClick={handleCopy} variant="outline">
          Copy
        </Button>
        <Button onClick={handleDownload} variant="outline">
          Download
        </Button>
      </div>

      <div className="overflow-hidden rounded-md border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Timestamp</TableHead>
              <TableHead>Level</TableHead>
              <TableHead>Domain</TableHead>
              <TableHead>Job</TableHead>
              <TableHead>Reason</TableHead>
              <TableHead>Message</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-sm text-muted-foreground">
                  Loading logs…
                </TableCell>
              </TableRow>
            )}
            {!isLoading && logLines.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-sm text-muted-foreground">
                  No log entries
                </TableCell>
              </TableRow>
            )}
            {logLines.map((line) => (
              <TableRow key={line.id}>
                <TableCell className="whitespace-nowrap text-xs">{formatDate(line.timestamp)}</TableCell>
                <TableCell>
                  <Badge variant={line.level === 'ERROR' ? 'destructive' : line.level === 'WARN' ? 'warning' : 'muted'}>
                    {line.level}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm">{line.domain ?? '—'}</TableCell>
                <TableCell className="font-mono text-xs">{line.jobId ?? '—'}</TableCell>
                <TableCell className="text-xs">{line.reasonCode ?? '—'}</TableCell>
                <TableCell className="text-sm">{line.message}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
