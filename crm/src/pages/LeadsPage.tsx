import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

import { fetchLeads, LeadBoardItem } from '../lib/api';
import { useAuth } from '../lib/auth-context';

const STATUSES: Array<LeadBoardItem['status']> = [
  'NEW',
  'CONTACTED',
  'QUALIFIED',
  'WON',
  'LOST',
];

const LeadsPage = () => {
  const { token } = useAuth();
  const { data } = useQuery({
    queryKey: ['leads'],
    queryFn: () => fetchLeads(token ?? ''),
    refetchInterval: 2000,
    enabled: Boolean(token),
  });

  const columns = useMemo(() => {
    const grouped: Record<string, LeadBoardItem[]> = {};
    (data ?? []).forEach((lead) => {
      const key = lead.status || 'NEW';
      grouped[key] = grouped[key] ?? [];
      grouped[key].push(lead);
    });
    return grouped;
  }, [data]);

  return (
    <div className="space-y-6 p-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Leads</h1>
        <p className="text-sm text-slate-500">
          Updated automatically — new submissions appear here within seconds.
        </p>
      </header>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {STATUSES.map((status) => (
          <section key={status} className="rounded border bg-white shadow-sm">
            <header className="border-b px-4 py-2 text-sm font-semibold uppercase text-slate-600">
              {status.replace('_', ' ')}
            </header>
            <div className="space-y-3 p-3">
              {(columns[status] ?? []).map((lead) => (
                <article key={lead.id} className="rounded border border-slate-200 bg-slate-50 p-3 shadow-sm">
                  <h2 className="text-sm font-medium text-slate-900">{lead.contact_name}</h2>
                  <p className="text-xs text-slate-500">Source: {lead.source ?? 'Unknown'}</p>
                  {lead.last_message_preview && (
                    <p className="mt-2 line-clamp-2 text-xs text-slate-600">{lead.last_message_preview}</p>
                  )}
                  <p className="mt-2 text-[11px] uppercase tracking-wide text-slate-400">
                    Created {new Date(lead.created_at).toLocaleString()}
                  </p>
                </article>
              ))}
              {!(columns[status] ?? []).length && (
                <p className="text-xs italic text-slate-400">No leads in this stage.</p>
              )}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
};

export default LeadsPage;
