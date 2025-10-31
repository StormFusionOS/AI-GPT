import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { cn } from '@/lib/utils';
import { Icon } from '@/components/icon';
import { api } from '@/services/api';
import type { BreadcrumbItem, MediaEntry, MediaListResponse } from '@/types';
import { useToast } from '@/components/ui/use-toast';

const textPreviewMimePrefixes = ['text/', 'application/json', 'application/xml'];

function formatBytes(size: number): string {
  if (size === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const exponent = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  const value = size / Math.pow(1024, exponent);
  return `${value.toFixed(value >= 10 || exponent === 0 ? 0 : 1)} ${units[exponent]}`;
}

function isTextLike(mimeType: string | null | undefined): boolean {
  if (!mimeType) return false;
  return textPreviewMimePrefixes.some((prefix) => mimeType.startsWith(prefix));
}

function splitPath(path: string): string[] {
  return path ? path.split('/').filter(Boolean) : [];
}

export function MediaBrowserPage() {
  const [root, setRoot] = useState<'media' | 'backup'>('media');
  const [currentPath, setCurrentPath] = useState<string>('');
  const [selectedEntry, setSelectedEntry] = useState<MediaEntry | null>(null);
  const { toast } = useToast();

  const { data, isLoading, isError, refetch } = useQuery<MediaListResponse, Error>({
    queryKey: ['media', root, currentPath],
    queryFn: () => api.getMediaList({ root, path: currentPath }),
    staleTime: 30_000,
  });

  useEffect(() => {
    if (isError) {
      toast({ title: 'Failed to load media listing', description: 'Please try again or check backend connectivity.', variant: 'destructive' });
    }
  }, [isError, toast]);

  useEffect(() => {
    setSelectedEntry(null);
  }, [root, currentPath]);

  const directories = useMemo(() => data?.entries.filter((entry) => entry.is_dir) ?? [], [data]);
  const entries = useMemo(() => data?.entries ?? [], [data]);

  const previewQuery = useQuery<string, Error>({
    queryKey: ['media-preview', root, selectedEntry?.path],
    queryFn: async () => {
      const result = await api.fetchMediaFile({ root, path: selectedEntry!.path, responseType: 'text' });
      return result as string;
    },
    enabled: Boolean(selectedEntry && !selectedEntry.is_dir && isTextLike(selectedEntry.mime_type)),
    staleTime: 0,
  });

  const breadcrumbs = useMemo(() => data?.breadcrumbs ?? [], [data]);

  function navigateToBreadcrumb(crumb: BreadcrumbItem) {
    setCurrentPath(crumb.path);
  }

  function openDirectory(entry: MediaEntry) {
    setCurrentPath(entry.path);
  }

  function handleRowClick(entry: MediaEntry) {
    if (entry.is_dir) {
      openDirectory(entry);
      return;
    }
    setSelectedEntry(entry);
  }

  function downloadSelected() {
    if (!selectedEntry) return;
    const url = api.getMediaDownloadUrl({ root, path: selectedEntry.path });
    window.open(url, '_blank', 'noopener');
  }

  const currentPathSegments = splitPath(data?.path ?? '');

  return (
    <div className="grid gap-4 lg:grid-cols-[280px,1fr]">
      <Card>
        <CardHeader>
          <CardTitle>Explorer</CardTitle>
          <CardDescription>Browse scraper media archives and daily backups.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Tabs
            value={root}
            onValueChange={(value) => {
              setRoot(value as 'media' | 'backup');
              setCurrentPath('');
            }}
          >
            <TabsList className="grid grid-cols-2">
              <TabsTrigger value="media">Media</TabsTrigger>
              <TabsTrigger value="backup">Backups</TabsTrigger>
            </TabsList>
          </Tabs>
          <div>
            <div className="text-xs font-semibold uppercase text-muted-foreground">Folders</div>
            <ScrollArea className="mt-2 h-64 rounded border">
              <ul className="divide-y divide-border text-sm">
                <li>
                  <button
                    type="button"
                    onClick={() => setCurrentPath('')}
                    className={cn(
                      'flex w-full items-center gap-2 px-3 py-2 text-left transition hover:bg-accent',
                      currentPathSegments.length === 0 && 'bg-accent text-accent-foreground',
                    )}
                  >
                    <Icon name="folder" className="h-4 w-4 text-amber-500" />
                    Root
                  </button>
                </li>
                {directories.map((entry) => (
                  <li key={entry.path}>
                    <button
                      type="button"
                      onClick={() => openDirectory(entry)}
                      className={cn(
                        'flex w-full items-center gap-2 px-3 py-2 text-left transition hover:bg-accent',
                        entry.path === currentPath && 'bg-accent text-accent-foreground',
                      )}
                    >
                      <Icon name="folder" className="h-4 w-4 text-amber-500" />
                      <span className="truncate">{entry.name}</span>
                    </button>
                  </li>
                ))}
                {directories.length === 0 && (
                  <li className="px-3 py-4 text-xs text-muted-foreground">No subdirectories in this folder.</li>
                )}
              </ul>
            </ScrollArea>
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader className="flex flex-row items-start justify-between gap-4">
            <div>
              <CardTitle>{root === 'media' ? 'Media Library' : 'Backup Archives'}</CardTitle>
              <CardDescription className="flex flex-wrap items-center gap-2 text-xs">
                {breadcrumbs.map((crumb, index) => (
                  <span key={crumb.path || 'root'} className="flex items-center gap-2">
                    {index > 0 && <Icon name="chevron-right" className="h-3 w-3" />}
                    <button
                      type="button"
                      className="text-foreground transition hover:underline"
                      onClick={() => navigateToBreadcrumb(crumb)}
                    >
                      {crumb.name || 'Root'}
                    </button>
                  </span>
                ))}
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => void refetch()}>
              Refresh
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[360px]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead className="hidden md:table-cell">Type</TableHead>
                    <TableHead className="hidden md:table-cell">Size</TableHead>
                    <TableHead className="hidden sm:table-cell">Modified</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading && (
                    <TableRow>
                      <TableCell colSpan={4} className="py-8 text-center text-sm text-muted-foreground">
                        Loading…
                      </TableCell>
                    </TableRow>
                  )}
                  {!isLoading && entries.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="py-8 text-center text-sm text-muted-foreground">
                        Folder is empty.
                      </TableCell>
                    </TableRow>
                  )}
                  {entries.map((entry) => (
                    <TableRow
                      key={entry.path}
                      onClick={() => handleRowClick(entry)}
                      className={cn(
                        'cursor-pointer transition hover:bg-accent',
                        selectedEntry?.path === entry.path && 'bg-accent text-accent-foreground',
                      )}
                    >
                      <TableCell className="flex items-center gap-2">
                        <Icon
                          name={entry.is_dir ? 'folder' : 'file'}
                          className={cn('h-4 w-4', entry.is_dir ? 'text-amber-500' : undefined)}
                        />
                        <span className="truncate">{entry.name}</span>
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        {entry.is_dir ? (
                          <Badge variant="outline">directory</Badge>
                        ) : (
                          <Badge variant="secondary">{entry.mime_type ?? 'binary/octet-stream'}</Badge>
                        )}
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        {entry.is_dir ? '—' : formatBytes(entry.size)}
                      </TableCell>
                      <TableCell className="hidden sm:table-cell">
                        {format(new Date(entry.modified_at), 'PPpp')}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Preview</CardTitle>
              <CardDescription>Quickly inspect files before downloading backups.</CardDescription>
            </div>
            <Button variant="secondary" size="sm" onClick={downloadSelected} disabled={!selectedEntry || selectedEntry.is_dir}>
              Download
            </Button>
          </CardHeader>
          <CardContent>
            {!selectedEntry && <p className="text-sm text-muted-foreground">Select a file to preview its contents.</p>}
            {selectedEntry && selectedEntry.is_dir && (
              <p className="text-sm text-muted-foreground">Folder selected. Choose a file to view preview details.</p>
            )}
            {selectedEntry && !selectedEntry.is_dir && (
              <div className="space-y-4">
                <div className="text-sm text-muted-foreground">
                  <div><span className="font-medium text-foreground">Name:</span> {selectedEntry.name}</div>
                  <div>
                    <span className="font-medium text-foreground">Type:</span> {selectedEntry.mime_type ?? 'binary/octet-stream'}
                  </div>
                  <div>
                    <span className="font-medium text-foreground">Size:</span> {formatBytes(selectedEntry.size)}
                  </div>
                  <div>
                    <span className="font-medium text-foreground">Modified:</span> {format(new Date(selectedEntry.modified_at), 'PPpp')}
                  </div>
                </div>
                {isTextLike(selectedEntry.mime_type) && (
                  <div className="rounded border bg-muted/40 p-3 text-xs">
                    {previewQuery.isLoading && <span className="text-muted-foreground">Loading preview…</span>}
                    {previewQuery.isError && (
                      <span className="text-destructive">Unable to load preview. Download the file to inspect contents.</span>
                    )}
                    {previewQuery.data && (
                      <pre className="max-h-64 overflow-auto whitespace-pre-wrap">{previewQuery.data.slice(0, 8000)}</pre>
                    )}
                  </div>
                )}
                {!isTextLike(selectedEntry.mime_type) && selectedEntry.mime_type?.startsWith('image/') && (
                  <img
                    src={api.getMediaDownloadUrl({ root, path: selectedEntry.path })}
                    alt={selectedEntry.name}
                    className="max-h-72 w-full rounded border object-contain"
                  />
                )}
                {!isTextLike(selectedEntry.mime_type) && selectedEntry.mime_type?.startsWith('audio/') && (
                  <audio controls className="w-full">
                    <source src={api.getMediaDownloadUrl({ root, path: selectedEntry.path })} type={selectedEntry.mime_type ?? undefined} />
                    Your browser does not support audio playback.
                  </audio>
                )}
                {!isTextLike(selectedEntry.mime_type) &&
                  selectedEntry.mime_type &&
                  !selectedEntry.mime_type.startsWith('image/') &&
                  !selectedEntry.mime_type.startsWith('audio/') && (
                    <p className="text-sm text-muted-foreground">
                      No inline preview available. Use the download button to inspect the file.
                    </p>
                  )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
