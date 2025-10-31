const drafts = [
  {
    id: 'draft-1',
    title: 'Spring SEO landing page refresh',
    author: 'Avery Johnson',
    status: 'in_review',
    updatedAt: new Date().toISOString(),
    summary: 'Hero copy updated with new conversion value props.'
  },
  {
    id: 'draft-2',
    title: 'FAQ schema for services page',
    author: 'AI assistant',
    status: 'draft',
    updatedAt: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    summary: 'Structured data to capture voice search queries.'
  }
];

export function ContentPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Content workspace</h1>
        <p className="text-sm text-muted-foreground">Manage AI-assisted drafts and publishing workflow.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {drafts.map((draft) => (
          <div key={draft.id} className="rounded-lg border border-border/60 bg-card p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">{draft.title}</h2>
              <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs capitalize text-primary">{draft.status.replace('_', ' ')}</span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">{draft.summary}</p>
            <p className="mt-4 text-xs text-muted-foreground">
              Updated {new Date(draft.updatedAt).toLocaleString()} · {draft.author}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
