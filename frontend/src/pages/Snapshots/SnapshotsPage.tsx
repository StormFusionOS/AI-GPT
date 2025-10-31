import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import DiffViewer from 'react-diff-viewer-continued';
import { Button } from '@/components/ui/button';
import { formatDate } from '@/lib/utils';

export function SnapshotsPage() {
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [diffSelection, setDiffSelection] = useState<{ a: string | null; b: string | null }>({ a: null, b: null });

  const snapshotsQuery = useQuery({ queryKey: ['snapshots'], queryFn: () => api.getSnapshots() });
  const detailQuery = useQuery({
    queryKey: ['snapshot', selectedId],
    queryFn: () => (selectedId ? api.getSnapshot(selectedId) : Promise.reject(new Error('no snapshot'))),
    enabled: Boolean(selectedId),
  });
  const diffQuery = useQuery({
    queryKey: ['snapshot-diff', diffSelection.a, diffSelection.b],
    queryFn: () =>
      diffSelection.a && diffSelection.b
        ? api.getSnapshotDiff(diffSelection.a, diffSelection.b)
        : Promise.reject(new Error('missing selections')),
    enabled: Boolean(diffSelection.a && diffSelection.b),
  });

  useEffect(() => {
    if (!selectedId && snapshotsQuery.data?.length) {
      setSelectedId(snapshotsQuery.data[0].id);
    }
  }, [selectedId, snapshotsQuery.data]);

  const filteredSnapshots = useMemo(() => {
    const list = snapshotsQuery.data ?? [];
    if (!search) return list;
    return list.filter((snapshot) =>
      [snapshot.domain, snapshot.path].some((value) => value.toLowerCase().includes(search.toLowerCase())),
    );
  }, [snapshotsQuery.data, search]);

  function handleDiffSelection(id: string) {
    setDiffSelection((prev) => {
      if (!prev.a || prev.a === id) {
        return { a: id, b: prev.b === id ? null : prev.b };
      }
      if (!prev.b || prev.b === id) {
        return { a: prev.a, b: prev.b === id ? null : id };
      }
      return { a: prev.a, b: id };
    });
  }

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle>Snapshots</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search domain or path" />
          <ScrollArea className="h-[520px] rounded border border-border">
            <div className="divide-y divide-border">
              {filteredSnapshots.map((snapshot) => {
                const isSelected = snapshot.id === selectedId;
                const inDiff = diffSelection.a === snapshot.id || diffSelection.b === snapshot.id;
                return (
                  <button
                    key={snapshot.id}
                    type="button"
                    onClick={() => setSelectedId(snapshot.id)}
                    className={`flex w-full flex-col items-start gap-1 px-4 py-3 text-left text-sm ${isSelected ? 'bg-accent' : ''}`}
                  >
                    <div className="flex w-full items-center justify-between">
                      <span className="font-medium">{snapshot.domain}</span>
                      <Button
                        variant={inDiff ? 'default' : 'outline'}
                        size="xs"
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          handleDiffSelection(snapshot.id);
                        }}
                      >
                        {inDiff ? 'Selected' : 'Diff'}
                      </Button>
                    </div>
                    <div className="text-xs text-muted-foreground">{snapshot.path}</div>
                    <div className="text-xs text-muted-foreground">{formatDate(snapshot.capturedAt)}</div>
                  </button>
                );
              })}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Snapshot Preview</CardTitle>
        </CardHeader>
        <CardContent>
          {!detailQuery.data && <div className="text-sm text-muted-foreground">Select a snapshot to preview.</div>}
          {detailQuery.data && (
            <Tabs defaultValue="html">
              <TabsList>
                <TabsTrigger value="html">HTML</TabsTrigger>
                <TabsTrigger value="screenshot" disabled={!detailQuery.data.screenshotUrl}>
                  Screenshot
                </TabsTrigger>
                <TabsTrigger value="diff" disabled={!diffSelection.a || !diffSelection.b}>
                  Diff
                </TabsTrigger>
              </TabsList>
              <TabsContent value="html" className="mt-4">
                <pre className="max-h-[480px] overflow-auto rounded bg-muted p-4 text-xs">
                  {detailQuery.data.html.slice(0, 15000)}
                  {detailQuery.data.html.length > 15000 && '\n… truncated'}
                </pre>
              </TabsContent>
              <TabsContent value="screenshot" className="mt-4">
                {detailQuery.data.screenshotUrl ? (
                  <img
                    src={detailQuery.data.screenshotUrl}
                    alt={`${detailQuery.data.domain} screenshot`}
                    className="w-full rounded border border-border"
                  />
                ) : (
                  <p className="text-sm text-muted-foreground">No screenshot available.</p>
                )}
              </TabsContent>
              <TabsContent value="diff" className="mt-4">
                {diffQuery.isLoading && <div className="text-sm text-muted-foreground">Loading diff…</div>}
                {diffQuery.data && (
                  <DiffViewer
                    oldValue={diffQuery.data.a.html}
                    newValue={diffQuery.data.b.html}
                    leftTitle={`${diffQuery.data.a.domain}${diffQuery.data.a.path}`}
                    rightTitle={`${diffQuery.data.b.domain}${diffQuery.data.b.path}`}
                    splitView
                  />
                )}
              </TabsContent>
            </Tabs>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
