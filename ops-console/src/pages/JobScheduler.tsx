import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  fetchSchedulerConfigs,
  runScheduledTask,
  SchedulerConfig,
  updateSchedulerConfigs,
} from '../lib/api';
import { useAuth } from '../lib/auth-context';

const formatDate = (value?: string | null) => {
  if (!value) return '—';
  return new Date(value).toLocaleString();
};

type Feedback = { type: 'success' | 'error'; message: string } | null;

type DraftState = Record<string, { crontab: string; enabled: boolean }>;

const JobSchedulerPage = () => {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [drafts, setDrafts] = useState<DraftState>({});
  const [feedback, setFeedback] = useState<Feedback>(null);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['scheduler-configs'],
    enabled: Boolean(token),
    queryFn: () => fetchSchedulerConfigs(token ?? ''),
  });

  useEffect(() => {
    setDrafts({});
  }, [data?.items]);

  const mutation = useMutation({
    mutationFn: (payload: { task_name: string; crontab: string; enabled: boolean }) =>
      updateSchedulerConfigs(token ?? '', [payload]),
    onSuccess: (response, variables) => {
      setFeedback({ type: 'success', message: `${variables.task_name} updated` });
      queryClient.setQueryData(['scheduler-configs'], response);
      setDrafts((current) => {
        const next = { ...current };
        delete next[variables.task_name];
        return next;
      });
    },
    onError: () => {
      setFeedback({ type: 'error', message: 'Failed to update schedule. Please retry.' });
    },
    onSettled: () => {
      void refetch();
    },
  });

  const runMutation = useMutation({
    mutationFn: (taskName: string) => runScheduledTask(token ?? '', taskName),
    onSuccess: (_, taskName) => {
      setFeedback({ type: 'success', message: `${taskName} enqueued` });
      void refetch();
    },
    onError: () => {
      setFeedback({ type: 'error', message: 'Unable to enqueue task.' });
    },
  });

  const rows: SchedulerConfig[] = useMemo(() => data?.items ?? [], [data?.items]);

  const handleToggle = (taskName: string, enabled: boolean) => {
    setDrafts((current) => ({
      ...current,
      [taskName]: { crontab: current[taskName]?.crontab ?? findConfig(taskName)?.crontab ?? '', enabled },
    }));
  };

  const handleCronChange = (taskName: string, crontab: string) => {
    const config = findConfig(taskName);
    setDrafts((current) => ({
      ...current,
      [taskName]: { crontab, enabled: current[taskName]?.enabled ?? config?.enabled ?? true },
    }));
  };

  const findConfig = (taskName: string) => rows.find((item) => item.task_name === taskName);

  const getDraft = (config: SchedulerConfig) => drafts[config.task_name] ?? {
    crontab: config.crontab,
    enabled: config.enabled,
  };

  const isDirty = (config: SchedulerConfig) => {
    const draft = drafts[config.task_name];
    if (!draft) return false;
    return draft.crontab !== config.crontab || draft.enabled !== config.enabled;
  };

  return (
    <div className="space-y-6 p-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Job Scheduler</h1>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Manage Celery beat intervals and trigger jobs immediately.
        </p>
      </header>
      {feedback && (
        <div
          className={`rounded-md border px-3 py-2 text-sm ${
            feedback.type === 'success'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-700/60 dark:bg-emerald-900/40 dark:text-emerald-200'
              : 'border-red-200 bg-red-50 text-red-700 dark:border-red-700/60 dark:bg-red-900/40 dark:text-red-200'
          }`}
        >
          {feedback.message}
        </div>
      )}
      {isLoading && <div className="text-sm text-slate-500">Loading scheduler configuration…</div>}
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-700 dark:bg-red-900/40 dark:text-red-100">
          Unable to load scheduler configuration.
        </div>
      )}
      {!isLoading && !error && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
            <thead className="bg-slate-100 dark:bg-slate-900/60">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">Task</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">Cron</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">Enabled</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">Last Run</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">Next Run</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">Updated By</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {rows.map((config) => {
                const draft = getDraft(config);
                const dirty = isDirty(config);
                return (
                  <tr key={config.id} className="bg-white dark:bg-slate-900/40">
                    <td className="px-4 py-3 font-medium capitalize text-slate-800 dark:text-slate-100">
                      {config.task_name.replace('_', ' ')}
                    </td>
                    <td className="px-4 py-3">
                      <input
                        aria-label={`Cron expression for ${config.task_name}`}
                        value={draft.crontab}
                        onChange={(event) => handleCronChange(config.task_name, event.target.value)}
                        className="w-40 rounded-md border border-slate-300 px-2 py-1 font-mono text-xs text-slate-700 focus:border-slate-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <label className="flex items-center space-x-2 text-slate-600 dark:text-slate-300">
                        <input
                          type="checkbox"
                          checked={draft.enabled}
                          onChange={(event) => handleToggle(config.task_name, event.target.checked)}
                          aria-label={`Toggle ${config.task_name}`}
                          className="h-4 w-4"
                        />
                        <span>{draft.enabled ? 'Enabled' : 'Disabled'}</span>
                      </label>
                    </td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{formatDate(config.last_run_at)}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{formatDate(config.next_run_at)}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                      {config.updated_by ?? 'system'}
                    </td>
                    <td className="px-4 py-3 space-x-2">
                      <button
                        type="button"
                        onClick={() => mutation.mutate({
                          task_name: config.task_name,
                          crontab: draft.crontab,
                          enabled: draft.enabled,
                        })}
                        disabled={!dirty || mutation.isLoading}
                        className="rounded-md border border-slate-300 bg-white px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        onClick={() => runMutation.mutate(config.task_name)}
                        disabled={runMutation.isLoading}
                        className="rounded-md bg-slate-900 px-3 py-1 text-xs font-medium text-white hover:bg-slate-700 disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200"
                      >
                        Run now
                      </button>
                    </td>
                  </tr>
                );
              })}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-center text-slate-500">
                    No scheduler entries configured.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default JobSchedulerPage;
