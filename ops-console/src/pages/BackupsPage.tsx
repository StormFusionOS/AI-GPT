import { useQuery } from '@tanstack/react-query';

import { fetchBackupRuns } from '../lib/api';
import { useAuth } from '../lib/auth-context';

const formatBytes = (value: number) => {
  if (value === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const power = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  const result = value / Math.pow(1024, power);
  return `${result.toFixed(1)} ${units[power]}`;
};

const BackupsPage = () => {
  const { token } = useAuth();
  const { data, isLoading, error } = useQuery({
    queryKey: ['backup-runs'],
    enabled: Boolean(token),
    queryFn: () => fetchBackupRuns(token ?? ''),
  });

  return (
    <div className="space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold">Backups</h1>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Overview of recent database and NAS synchronization jobs.
        </p>
      </header>
      {isLoading && <div className="text-sm text-slate-500">Loading backup history…</div>}
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-700 dark:bg-red-900/40 dark:text-red-100">
          Failed to load backups. Please retry.
        </div>
      )}
      {!isLoading && !error && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-700">
            <thead className="bg-slate-100 dark:bg-slate-900/60">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">Type</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">Started</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">Finished</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">Bytes</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">Status</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {data?.items.map((run) => {
                const statusColor = run.ok ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400';
                const verifyLabel =
                  run.verify_ok === undefined || run.verify_ok === null
                    ? '—'
                    : run.verify_ok
                    ? 'Verified'
                    : 'Verification failed';
                return (
                  <tr key={run.id} className="bg-white dark:bg-slate-900/40">
                    <td className="px-4 py-2 font-medium capitalize text-slate-800 dark:text-slate-100">{run.run_type.replace('_', ' ')}</td>
                    <td className="px-4 py-2 text-slate-600 dark:text-slate-300">{new Date(run.started_at).toLocaleString()}</td>
                    <td className="px-4 py-2 text-slate-600 dark:text-slate-300">
                      {run.finished_at ? new Date(run.finished_at).toLocaleString() : '—'}
                    </td>
                    <td className="px-4 py-2 text-slate-600 dark:text-slate-300">{formatBytes(run.bytes)}</td>
                    <td className={`px-4 py-2 font-medium ${statusColor}`}>
                      {run.ok ? 'OK' : 'Failed'}
                      <span className="ml-2 text-xs text-slate-500 dark:text-slate-400">{verifyLabel}</span>
                    </td>
                    <td className="px-4 py-2 text-slate-600 dark:text-slate-300">
                      {run.message ?? '—'}
                    </td>
                  </tr>
                );
              })}
              {data?.items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-slate-500">
                    No backup runs recorded yet.
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

export default BackupsPage;
