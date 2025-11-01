import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import DiffViewer from '../components/DiffViewer';
import {
  ReviewSuggestion,
  ReviewType,
  approveSuggestion,
  fetchReviewSuggestions,
  rejectSuggestion,
} from '../lib/api';
import { useAuth } from '../lib/auth-context';

const typeFilters: (ReviewType | 'all')[] = ['all', 'meta', 'faq', 'jsonld', 'link'];

const formatTitle = (suggestion: ReviewSuggestion) => {
  switch (suggestion.type) {
    case 'meta':
      return `Meta update for ${suggestion.target}`;
    case 'faq':
      return `FAQ addition for ${suggestion.target}`;
    case 'jsonld':
      return `JSON-LD update for ${suggestion.target}`;
    case 'link':
      return `Internal link suggestion for ${suggestion.target}`;
    default:
      return `Suggestion for ${suggestion.target}`;
  }
};

const MetaPreview = ({ suggestion }: { suggestion: ReviewSuggestion }) => {
  const current = (suggestion.current_state.meta as Record<string, unknown>) ?? {};
  const proposed = suggestion.payload as Record<string, unknown>;
  const title = typeof proposed.title === 'string' ? proposed.title : '';
  const description = typeof proposed.description === 'string' ? proposed.description : '';

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-200">Title</h4>
          <p className="text-sm text-slate-700 dark:text-slate-100">{title}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">Characters: {title.length}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-200">Description</h4>
          <p className="text-sm text-slate-700 dark:text-slate-100">{description}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">Characters: {description.length}</p>
        </div>
      </div>
      <DiffViewer before={current} after={proposed} format="json" beforeLabel="Current meta" afterLabel="Suggested meta" />
    </div>
  );
};

const FAQPreview = ({ suggestion }: { suggestion: ReviewSuggestion }) => {
  const current = (suggestion.current_state.faqs as Array<Record<string, unknown>>) ?? [];
  const proposed = suggestion.payload as Record<string, unknown>;

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-200">Existing FAQs</h4>
        {current.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No FAQs published yet.</p>
        ) : (
          <ul className="space-y-2 text-sm text-slate-700 dark:text-slate-100">
            {current.map((item, idx) => (
              <li key={idx} className="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
                <strong>{item.question as string}</strong>
                <p>{item.answer as string}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm dark:border-emerald-900 dark:bg-emerald-950">
        <h4 className="font-semibold text-emerald-700 dark:text-emerald-300">Proposed FAQ</h4>
        <p className="font-medium">{proposed.question as string}</p>
        <p>{proposed.answer as string}</p>
      </div>
    </div>
  );
};

const JsonPreview = ({ suggestion }: { suggestion: ReviewSuggestion }) => {
  const current = suggestion.current_state.jsonld ?? {};
  const payload = suggestion.payload;
  const data = (payload.data as Record<string, unknown>) ?? payload;

  return <DiffViewer before={current} after={data} format="json" beforeLabel="Current JSON-LD" afterLabel="Suggested JSON-LD" />;
};

const LinkPreview = ({ suggestion }: { suggestion: ReviewSuggestion }) => {
  const current = (suggestion.current_state.links as Array<Record<string, unknown>>) ?? [];
  const payload = suggestion.payload as Record<string, unknown>;

  return (
    <div className="space-y-3">
      <div>
        <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-200">Current Internal Links ({current.length})</h4>
        {current.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No tracked links yet.</p>
        ) : (
          <ul className="space-y-1 text-sm text-slate-700 dark:text-slate-100">
            {current.map((item, idx) => (
              <li key={idx} className="rounded-md border border-slate-200 bg-white p-2 dark:border-slate-800 dark:bg-slate-900">
                {(item.anchor as string) ?? 'Anchor'} → {(item.target as string) ?? 'Target'}
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm dark:border-emerald-900 dark:bg-emerald-950">
        <h4 className="font-semibold text-emerald-700 dark:text-emerald-300">Proposed Link</h4>
        <p className="font-medium">Anchor: {(payload.anchor as string) ?? '—'}</p>
        <p>Destination: {(payload.target as string) ?? '—'}</p>
        <p>Source: {(payload.source as string) ?? suggestion.target}</p>
      </div>
    </div>
  );
};

const ReviewQueuePage = () => {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<ReviewType | 'all'>('all');

  const { data, isLoading, isError } = useQuery(
    ['review', filter],
    () =>
      fetchReviewSuggestions(token ?? '', {
        status: 'pending',
        type: filter === 'all' ? undefined : filter,
      }),
    {
      enabled: Boolean(token),
    }
  );

  const approve = useMutation((id: number) => approveSuggestion(token ?? '', id), {
    onSuccess: () => queryClient.invalidateQueries(['review']),
  });
  const reject = useMutation(({ id, reason }: { id: number; reason: string }) => rejectSuggestion(token ?? '', id, reason), {
    onSuccess: () => queryClient.invalidateQueries(['review']),
  });

  const suggestions = useMemo(() => data?.items ?? [], [data]);

  const onApprove = (id: number) => approve.mutate(id);
  const onReject = (id: number) => {
    const reason = window.prompt('Provide a reason for rejection:');
    if (!reason) return;
    reject.mutate({ id, reason });
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Review Queue</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Approve or reject AI-generated suggestions before publishing to production.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {typeFilters.map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setFilter(option)}
              className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
                filter === option
                  ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
                  : 'bg-slate-200 text-slate-700 hover:bg-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
              }`}
            >
              {option === 'all' ? 'All' : option.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <p className="text-sm text-slate-500">Loading suggestions…</p>
      ) : isError ? (
        <p className="text-sm text-red-600">Unable to load suggestions. Check API connectivity.</p>
      ) : suggestions.length === 0 ? (
        <p className="text-sm text-slate-500">No pending suggestions 🎉</p>
      ) : (
        <div className="space-y-6">
          {suggestions.map((suggestion) => (
            <article
              key={suggestion.id}
              className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
            >
              <header className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{formatTitle(suggestion)}</h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Created {new Date(suggestion.created_at).toLocaleString()} · Anomaly {suggestion.anomaly_id ?? '—'}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => onApprove(suggestion.id)}
                    disabled={approve.isLoading || reject.isLoading}
                    className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {approve.isLoading ? 'Applying…' : 'Approve'}
                  </button>
                  <button
                    type="button"
                    onClick={() => onReject(suggestion.id)}
                    disabled={approve.isLoading || reject.isLoading}
                    className="rounded-md bg-red-100 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-200 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-red-900/30 dark:text-red-300 dark:hover:bg-red-900/50"
                  >
                    Reject
                  </button>
                </div>
              </header>

              {suggestion.type === 'meta' && <MetaPreview suggestion={suggestion} />}
              {suggestion.type === 'faq' && <FAQPreview suggestion={suggestion} />}
              {suggestion.type === 'jsonld' && <JsonPreview suggestion={suggestion} />}
              {suggestion.type === 'link' && <LinkPreview suggestion={suggestion} />}
              {suggestion.type !== 'meta' &&
                suggestion.type !== 'faq' &&
                suggestion.type !== 'jsonld' &&
                suggestion.type !== 'link' && (
                  <DiffViewer before={suggestion.current_state} after={suggestion.payload} />
                )}

              {suggestion.decision_reason && (
                <p className="text-xs text-slate-500">Decision: {suggestion.decision_reason}</p>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
};

export default ReviewQueuePage;
