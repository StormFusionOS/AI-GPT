import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { DiffViewer } from '@/components/DiffViewer';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import type { ReviewChange } from '@/types';
import { formatDate } from '@/lib/utils';

function statusVariant(status: ReviewChange['status']) {
  switch (status) {
    case 'approved':
      return 'success' as const;
    case 'rejected':
      return 'destructive' as const;
    case 'applied':
      return 'secondary' as const;
    default:
      return 'outline' as const;
  }
}

export function ReviewQueuePage() {
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [reviewNote, setReviewNote] = useState('');
  const [diffSplitView, setDiffSplitView] = useState(true);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: reviewItems } = useQuery({
    queryKey: ['review-queue', statusFilter],
    queryFn: () => api.getReviewQueue(statusFilter === 'all' ? undefined : statusFilter),
  });

  const activeItem = useMemo(() => {
    if (!reviewItems || reviewItems.length === 0) {
      return undefined;
    }
    if (selectedId) {
      return reviewItems.find((item) => item.id === selectedId) ?? reviewItems[0];
    }
    return reviewItems[0];
  }, [reviewItems, selectedId]);

  const { data: changeDetail } = useQuery({
    queryKey: ['review-change', activeItem?.id],
    queryFn: () => api.getReviewChange(activeItem!.id),
    enabled: Boolean(activeItem?.id),
  });

  const { data: diffData, isError: diffError } = useQuery({
    queryKey: [
      'review-diff',
      changeDetail?.contentId,
      changeDetail?.currentVersionId,
      changeDetail?.proposedVersionId,
    ],
    queryFn: () =>
      api.fetchDiff({
        contentId: changeDetail!.contentId,
        version1: changeDetail!.currentVersionId,
        version2: changeDetail!.proposedVersionId,
      }),
    enabled: Boolean(changeDetail?.contentId),
  });

  const approveMutation = useMutation({
    mutationFn: (payload: { id: string; note?: string }) => api.approveReviewChange(payload.id, payload.note),
    onSuccess: () => {
      toast({ title: 'Change approved', description: 'Marked for publishing.' });
      queryClient.invalidateQueries({ queryKey: ['review-queue'] });
      if (changeDetail) {
        queryClient.invalidateQueries({ queryKey: ['review-change', changeDetail.id] });
      }
    },
    onError: (error) => {
      toast({ title: 'Failed to approve change', description: String(error), variant: 'destructive' });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (payload: { id: string; note?: string }) => api.rejectReviewChange(payload.id, payload.note),
    onSuccess: () => {
      toast({ title: 'Change rejected', description: 'The AI suggestion was dismissed.' });
      queryClient.invalidateQueries({ queryKey: ['review-queue'] });
      if (changeDetail) {
        queryClient.invalidateQueries({ queryKey: ['review-change', changeDetail.id] });
      }
    },
    onError: (error) => {
      toast({ title: 'Failed to reject change', description: String(error), variant: 'destructive' });
    },
  });

  const handleReview = (action: 'approve' | 'reject') => {
    if (!changeDetail) return;
    const payload = { id: changeDetail.id, note: reviewNote.trim() || undefined };
    if (action === 'approve') {
      approveMutation.mutate(payload);
    } else {
      rejectMutation.mutate(payload);
    }
    setReviewNote('');
  };

  const diffLanguage = changeDetail?.changeType.includes('schema') ? 'json' : 'html';

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Review Queue</h1>
          <p className="text-sm text-muted-foreground">
            Compare AI recommendations with live content before promoting changes to production.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="status-filter" className="text-sm text-muted-foreground">
            Status
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="applied">Applied</option>
            <option value="all">All</option>
          </select>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]">
        <Card className="h-full">
          <CardHeader>
            <CardTitle>Queued Changes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {reviewItems?.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedId(item.id)}
                  className={`w-full rounded-md border px-4 py-3 text-left transition hover:bg-muted ${
                    activeItem?.id === item.id ? 'border-primary bg-muted' : 'border-border'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold">{item.title}</p>
                      <p className="text-xs text-muted-foreground">{item.module} · {item.changeType}</p>
                    </div>
                    <Badge variant={statusVariant(item.status)} className="uppercase">
                      {item.status}
                    </Badge>
                  </div>
                  <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">{item.summary}</p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Submitted {formatDate(item.createdAt)} by {item.submittedBy}
                  </p>
                </button>
              ))}
              {!reviewItems?.length && (
                <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
                  No changes found for this filter.
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="h-full">
          <CardHeader>
            <CardTitle>Change Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!changeDetail && <div className="text-sm text-muted-foreground">Select a change to review details.</div>}
            {changeDetail && (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">{changeDetail.summary}</span>
                  <span>•</span>
                  <span>Priority: {String(changeDetail.metadata.priority ?? 'normal')}</span>
                  <span>•</span>
                  <span>
                    Page:{' '}
                    {typeof changeDetail.metadata.pageUrl === 'string'
                      ? changeDetail.metadata.pageUrl
                      : 'Not specified'}
                  </span>
                </div>
                {diffError && (
                  <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-xs text-destructive">
                    Unable to load diff for this change. Confirm the version history is still available.
                  </div>
                )}
                {diffData && (
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <div>
                          <span className="font-semibold text-foreground">{diffData.versionA.label}</span>
                          <span className="ml-2">· {formatDate(diffData.versionA.createdAt)}</span>
                        </div>
                        <span className="hidden text-muted-foreground sm:inline">→</span>
                        <div>
                          <span className="font-semibold text-foreground">{diffData.versionB.label}</span>
                          <span className="ml-2">· {formatDate(diffData.versionB.createdAt)}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Switch id="diff-view" checked={diffSplitView} onCheckedChange={setDiffSplitView} />
                        <Label htmlFor="diff-view" className="text-xs text-muted-foreground">
                          Split view
                        </Label>
                      </div>
                    </div>
                    <DiffViewer
                      oldValue={diffData.versionA.content}
                      newValue={diffData.versionB.content}
                      language={diffLanguage as 'html' | 'json' | 'text'}
                      splitView={diffSplitView}
                    />
                  </div>
                )}

                <div className="space-y-2">
                  <label htmlFor="review-note" className="text-sm font-medium text-foreground">
                    Reviewer note (optional)
                  </label>
                  <Textarea
                    id="review-note"
                    value={reviewNote}
                    onChange={(event) => setReviewNote(event.target.value)}
                    placeholder="Summarize actions taken or follow-up steps for the team."
                    className="min-h-[120px]"
                  />
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    onClick={() => handleReview('approve')}
                    disabled={approveMutation.isLoading || !changeDetail || changeDetail.status !== 'pending'}
                  >
                    {approveMutation.isLoading ? 'Approving…' : 'Approve'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => handleReview('reject')}
                    disabled={rejectMutation.isLoading || !changeDetail || changeDetail.status !== 'pending'}
                  >
                    {rejectMutation.isLoading ? 'Rejecting…' : 'Reject'}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
