import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { formatDate, formatDuration } from '@/lib/utils';
import { JobStatusBadge } from '@/components/JobStatusBadge';
import { ReasonCodeBadge } from '@/components/ReasonCodeBadge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import type { JobStatus } from '@/types';

const JOB_TABS: JobStatus[] = ['running', 'pending', 'completed', 'failed'];

export function JobsPage() {
  const [status, setStatus] = useState<JobStatus>('running');
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const jobsQuery = useQuery({
    queryKey: ['jobs', status],
    queryFn: () => api.getJobs(status),
  });

  const jobDetailQuery = useQuery({
    queryKey: ['job', selectedJobId],
    queryFn: () => (selectedJobId ? api.getJob(selectedJobId) : Promise.reject(new Error('no job'))),
    enabled: Boolean(selectedJobId),
  });

  return (
    <div>
      <Tabs value={status} onValueChange={(value) => setStatus(value as JobStatus)}>
        <TabsList>
          {JOB_TABS.map((tab) => (
            <TabsTrigger key={tab} value={tab}>
              {tab.toUpperCase()}
            </TabsTrigger>
          ))}
        </TabsList>
        {JOB_TABS.map((tab) => (
          <TabsContent key={tab} value={tab}>
            <div className="mt-4 overflow-hidden rounded-md border border-border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Domain</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Started</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobsQuery.isLoading && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-sm text-muted-foreground">
                        Loading jobs…
                      </TableCell>
                    </TableRow>
                  )}
                  {!jobsQuery.isLoading && jobsQuery.data?.items.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-sm text-muted-foreground">
                        No jobs in this state
                      </TableCell>
                    </TableRow>
                  )}
                  {jobsQuery.data?.items.map((job) => (
                    <TableRow key={job.id} className="cursor-pointer" onClick={() => setSelectedJobId(job.id)}>
                      <TableCell className="font-mono text-xs">{job.id}</TableCell>
                      <TableCell>{job.type}</TableCell>
                      <TableCell>{job.domain}</TableCell>
                      <TableCell>
                        <JobStatusBadge status={job.status} />
                      </TableCell>
                      <TableCell>{formatDate(job.startedAt)}</TableCell>
                      <TableCell>{formatDuration(job.durationSeconds)}</TableCell>
                      <TableCell>
                        <ReasonCodeBadge reason={job.reasonCode} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>
        ))}
      </Tabs>

      <Dialog open={Boolean(selectedJobId)} onOpenChange={(open) => !open && setSelectedJobId(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Job Details</DialogTitle>
          </DialogHeader>
          {jobDetailQuery.isLoading && <div className="text-sm text-muted-foreground">Loading job…</div>}
          {jobDetailQuery.data && (
            <div className="space-y-4">
              <div className="grid gap-2 text-sm">
                <div>
                  <span className="font-semibold">Job ID:</span> {jobDetailQuery.data.id}
                </div>
                <div>
                  <span className="font-semibold">Type:</span> {jobDetailQuery.data.type}
                </div>
                <div>
                  <span className="font-semibold">Domain:</span> {jobDetailQuery.data.domain}
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold">Status:</span> <JobStatusBadge status={jobDetailQuery.data.status} />
                  <ReasonCodeBadge reason={jobDetailQuery.data.reasonCode} />
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold">Parameters</h3>
                <pre className="mt-2 max-h-40 overflow-auto rounded bg-muted p-3 text-xs">
                  {JSON.stringify(jobDetailQuery.data.params, null, 2)}
                </pre>
              </div>
              <div>
                <h3 className="text-sm font-semibold">Logs</h3>
                <ScrollArea className="max-h-48 rounded border border-border">
                  <div className="space-y-1 p-3 text-xs font-mono">
                    {jobDetailQuery.data.logs.map((line, index) => (
                      <div key={index}>{line}</div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
              {jobDetailQuery.data.artifacts.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold">Artifacts</h3>
                  <ul className="list-disc space-y-1 pl-5 text-sm">
                    {jobDetailQuery.data.artifacts.map((artifact) => (
                      <li key={artifact.id}>
                        <a href={artifact.url} target="_blank" rel="noreferrer" className="text-primary hover:underline">
                          {artifact.label}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="flex items-center justify-end gap-2">
                <Button disabled variant="outline">
                  Cancel
                </Button>
                <Button disabled>Retry</Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Backend actions are disabled in mock mode. Connect the real API to enable retry/cancel controls.
              </p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
