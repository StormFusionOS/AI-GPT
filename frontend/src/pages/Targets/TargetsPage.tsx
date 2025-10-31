import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { Target } from '@/types';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { MoreHorizontal, PlusCircle } from 'lucide-react';
import { RobotsChip } from '@/components/RobotsChip';
import { useToast } from '@/components/ui/use-toast';

const TAG_OPTIONS: Target['tags'] = ['citations', 'backlinks', 'competitor', 'serp', 'mentions'];

export function TargetsPage() {
  const queryClient = useQueryClient();
  const { data = [], isLoading } = useQuery({ queryKey: ['targets'], queryFn: api.getTargets });
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [tagFilter, setTagFilter] = useState<string>('all');
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [draft, setDraft] = useState({ domain: '', depth: 2, cadence: '0 2 * * *', renderBudget: 5, tags: [] as Target['tags'], notes: '' });

  const createMutation = useMutation({
    mutationFn: api.createTarget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['targets'] });
      toast({ title: 'Target added', description: `${draft.domain} scheduled.` });
      setIsAddOpen(false);
      setDraft({ domain: '', depth: 2, cadence: '0 2 * * *', renderBudget: 5, tags: [], notes: '' });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<Target> }) => api.updateTarget(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['targets'] });
      toast({ title: 'Target updated' });
    },
  });

  const runMutation = useMutation({
    mutationFn: api.runTarget,
    onSuccess: () => {
      toast({ title: 'Run enqueued' });
    },
  });

  const filteredTargets = useMemo(() => {
    return data
      .filter((target) =>
        search ? target.domain.toLowerCase().includes(search.toLowerCase()) || target.tags.some((tag) => tag.includes(search.toLowerCase())) : true,
      )
      .filter((target) => (tagFilter === 'all' ? true : target.tags.includes(tagFilter as Target['tags'][number])));
  }, [data, search, tagFilter]);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft.domain) {
      toast({ title: 'Domain required', variant: 'destructive' });
      return;
    }
    const id = typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : `tgt-${Date.now()}`;
    createMutation.mutate({
      domain: draft.domain,
      depth: Number(draft.depth),
      cadence: draft.cadence,
      renderBudget: Number(draft.renderBudget),
      tags: draft.tags,
      notes: draft.notes,
      status: 'enabled',
      lastScrape: null,
      robotsStatus: 'ok',
      nextRun: new Date().toISOString(),
      id,
    });
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-1 gap-2">
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search domains or tags"
            className="max-w-sm"
            aria-label="Search targets"
          />
          <select
            aria-label="Filter by tag"
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            value={tagFilter}
            onChange={(event) => setTagFilter(event.target.value)}
          >
            <option value="all">All Tags</option>
            {TAG_OPTIONS.map((tag) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
            ))}
          </select>
        </div>
        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button>
              <PlusCircle className="mr-2 h-4 w-4" /> Add Target
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Target</DialogTitle>
            </DialogHeader>
            <form id="add-target-form" onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="domain">Domain</Label>
                <Input id="domain" value={draft.domain} onChange={(event) => setDraft((prev) => ({ ...prev, domain: event.target.value }))} required />
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="depth">Depth</Label>
                  <Input
                    id="depth"
                    type="number"
                    min={1}
                    value={draft.depth}
                    onChange={(event) => setDraft((prev) => ({ ...prev, depth: Number(event.target.value) }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="renderBudget">Render Budget</Label>
                  <Input
                    id="renderBudget"
                    type="number"
                    min={1}
                    value={draft.renderBudget}
                    onChange={(event) => setDraft((prev) => ({ ...prev, renderBudget: Number(event.target.value) }))}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="cadence">Cadence (CRON)</Label>
                <Input
                  id="cadence"
                  value={draft.cadence}
                  onChange={(event) => setDraft((prev) => ({ ...prev, cadence: event.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Tags</Label>
                <div className="flex flex-wrap gap-2">
                  {TAG_OPTIONS.map((tag) => {
                    const selected = draft.tags.includes(tag);
                    return (
                      <Button
                        key={tag}
                        type="button"
                        variant={selected ? 'default' : 'outline'}
                        size="sm"
                        onClick={() =>
                          setDraft((prev) => ({
                            ...prev,
                            tags: selected
                              ? prev.tags.filter((t) => t !== tag)
                              : [...prev.tags, tag],
                          }))
                        }
                      >
                        {tag}
                      </Button>
                    );
                  })}
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  value={draft.notes}
                  onChange={(event) => setDraft((prev) => ({ ...prev, notes: event.target.value }))}
                />
              </div>
            </form>
            <DialogFooter>
              <Button form="add-target-form" type="submit" disabled={createMutation.isPending}>
                Save Target
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="overflow-hidden rounded-md border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Domain</TableHead>
              <TableHead>Tags</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Robots</TableHead>
              <TableHead>Last Scrape</TableHead>
              <TableHead>Next Run</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-sm text-muted-foreground">
                  Loading targets…
                </TableCell>
              </TableRow>
            )}
            {!isLoading && filteredTargets.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-sm text-muted-foreground">
                  No targets found
                </TableCell>
              </TableRow>
            )}
            {filteredTargets.map((target) => (
              <TableRow key={target.id}>
                <TableCell className="font-medium">{target.domain}</TableCell>
                <TableCell className="space-x-1">
                  {target.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </TableCell>
                <TableCell>
                  <Badge variant={target.status === 'enabled' ? 'success' : 'muted'}>
                    {target.status.toUpperCase()}
                  </Badge>
                </TableCell>
                <TableCell>
                  <RobotsChip status={target.robotsStatus} />
                </TableCell>
                <TableCell>{formatDate(target.lastScrape)}</TableCell>
                <TableCell>{formatDate(target.nextRun)}</TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" aria-label={`Actions for ${target.domain}`}>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onSelect={() =>
                          runMutation.mutate(target.id, {
                            onError: () => toast({ title: 'Failed to run target', variant: 'destructive' }),
                          })
                        }
                      >
                        Run Now
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onSelect={() =>
                          updateMutation.mutate({
                            id: target.id,
                            payload: { status: target.status === 'enabled' ? 'disabled' : 'enabled' },
                          })
                        }
                      >
                        {target.status === 'enabled' ? 'Disable' : 'Enable'}
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onSelect={() =>
                          updateMutation.mutate({ id: target.id, payload: { notes: `${target.notes ?? ''} (edited)` } })
                        }
                      >
                        Edit
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
