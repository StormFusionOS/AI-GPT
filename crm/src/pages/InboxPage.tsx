import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { fetchLeadInteractions, fetchLeads, InteractionItem } from '../lib/api';
import { useAuth } from '../lib/auth-context';

const InboxPage = () => {
  const { token } = useAuth();
  const { data: leads } = useQuery({
    queryKey: ['leads'],
    queryFn: () => fetchLeads(token ?? ''),
    refetchInterval: 2000,
    enabled: Boolean(token),
  });
  const [activeLeadId, setActiveLeadId] = useState<string | null>(null);

  const leadOptions = useMemo(() => leads ?? [], [leads]);
  const resolvedLeadId = activeLeadId ?? leadOptions[0]?.id ?? null;

  const { data: interactions } = useQuery<InteractionItem[]>({
    queryKey: ['lead-interactions', resolvedLeadId],
    queryFn: () => fetchLeadInteractions(resolvedLeadId!, token ?? ''),
    refetchInterval: 2000,
    enabled: Boolean(token && resolvedLeadId),
  });

  return (
    <div className="flex h-full flex-col md:flex-row">
      <aside className="w-full border-r bg-slate-50 md:w-64">
        <div className="border-b px-4 py-3 text-sm font-semibold uppercase text-slate-600">Threads</div>
        <ul className="divide-y">
          {leadOptions.map((lead) => (
            <li key={lead.id}>
              <button
                type="button"
                onClick={() => setActiveLeadId(lead.id)}
                className={`flex w-full flex-col items-start px-4 py-3 text-left text-sm ${
                  lead.id === resolvedLeadId ? 'bg-white font-semibold shadow-inner' : 'text-slate-600'
                }`}
              >
                <span>{lead.contact_name}</span>
                <span className="text-xs text-slate-400">{lead.last_message_preview ?? 'No messages yet'}</span>
              </button>
            </li>
          ))}
          {!leadOptions.length && <li className="px-4 py-6 text-sm text-slate-400">No active conversations.</li>}
        </ul>
      </aside>
      <main className="flex flex-1 flex-col">
        <header className="border-b px-6 py-4">
          <h1 className="text-xl font-semibold">Inbox</h1>
          <p className="text-sm text-slate-500">Inbound and auto replies appear here instantly.</p>
        </header>
        <div className="flex-1 space-y-3 overflow-y-auto bg-slate-100 p-4">
          {(interactions ?? []).map((interaction) => (
            <article
              key={interaction.id}
              className={`max-w-lg rounded px-4 py-2 text-sm shadow ${
                interaction.interaction_type.endsWith('_OUT')
                  ? 'ml-auto bg-emerald-500 text-white'
                  : 'bg-white text-slate-800'
              }`}
            >
              <div className="text-xs uppercase tracking-wide text-slate-400">
                {interaction.interaction_type.replace('_', ' ')}
              </div>
              <p>{interaction.content}</p>
              <div className="text-right text-[11px] text-slate-300">
                {new Date(interaction.occurred_at).toLocaleTimeString()}
              </div>
            </article>
          ))}
          {resolvedLeadId && !(interactions ?? []).length && (
            <p className="text-sm text-slate-500">No messages yet for this lead.</p>
          )}
        </div>
      </main>
    </div>
  );
};

export default InboxPage;
