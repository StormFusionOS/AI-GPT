import { useMemo } from 'react';

export type LeadStatus = 'new' | 'contacted' | 'quoted' | 'won' | 'lost';

export interface LeadSummary {
  id: string;
  name: string;
  company?: string;
  status: LeadStatus;
  source?: string;
  value?: number;
}

interface LeadsKanbanProps {
  leads: LeadSummary[];
}

const STATUS_COLUMNS: Array<{ key: LeadStatus; label: string }> = [
  { key: 'new', label: 'New' },
  { key: 'contacted', label: 'Contacted' },
  { key: 'quoted', label: 'Quoted' },
  { key: 'won', label: 'Won' },
  { key: 'lost', label: 'Lost' },
];

export function LeadsKanban({ leads }: LeadsKanbanProps) {
  const grouped = useMemo(() => {
    const buckets = STATUS_COLUMNS.reduce<Record<LeadStatus, LeadSummary[]>>(
      (accumulator, column) => ({ ...accumulator, [column.key]: [] }),
      {} as Record<LeadStatus, LeadSummary[]>,
    );
    leads.forEach((lead) => {
      buckets[lead.status]?.push(lead);
    });
    return buckets;
  }, [leads]);

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5" aria-label="Leads Kanban">
      {STATUS_COLUMNS.map((column) => (
        <section key={column.key} aria-label={`${column.label} column`} className="rounded-md border bg-card p-3">
          <header className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">{column.label}</h2>
            <span className="text-xs text-muted-foreground">{grouped[column.key]?.length ?? 0}</span>
          </header>
          <div className="space-y-2">
            {grouped[column.key]?.map((lead) => (
              <article
                key={lead.id}
                className="rounded-md border border-border bg-background p-3 text-sm shadow-sm"
                aria-label={`${lead.name} card`}
              >
                <p className="font-medium">{lead.name}</p>
                {lead.company && <p className="text-xs text-muted-foreground">{lead.company}</p>}
                {lead.source && <p className="text-xs text-muted-foreground">Source: {lead.source}</p>}
                {typeof lead.value === 'number' && (
                  <p className="text-xs text-muted-foreground">Value: ${lead.value.toLocaleString()}</p>
                )}
              </article>
            ))}
            {grouped[column.key]?.length === 0 && (
              <p className="rounded-md border border-dashed p-3 text-xs text-muted-foreground">No leads in this stage.</p>
            )}
          </div>
        </section>
      ))}
    </div>
  );
}
