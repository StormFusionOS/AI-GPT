import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo } from 'react';

import { fetchSecurityHygiene, triggerSecurityScan } from '../lib/api';
import { useAuth } from '../lib/auth-context';

const SecurityHygienePage = () => {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['security-hygiene'],
    queryFn: () => fetchSecurityHygiene(token ?? ''),
    enabled: Boolean(token),
  });

  const mutation = useMutation({
    mutationFn: () => triggerSecurityScan(token ?? ''),
    onSuccess: (payload) => {
      queryClient.setQueryData(['security-hygiene'], payload);
    },
  });

  const lastScanDisplay = useMemo(() => {
    if (!data?.last_scan) {
      return 'No scans yet';
    }
    return new Date(data.last_scan).toLocaleString();
  }, [data?.last_scan]);

  return (
    <div className="space-y-6 p-6">
      <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Security Hygiene</h1>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Review the latest integrity baseline and rerun scans after deployments.
          </p>
        </div>
        <button
          type="button"
          onClick={() => mutation.mutate()}
          disabled={!token || mutation.isLoading}
          className="inline-flex items-center rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm disabled:cursor-not-allowed disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
        >
          {mutation.isLoading ? 'Scanning…' : 'Scan Now'}
        </button>
      </header>

      <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-lg font-semibold">Baseline Overview</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Last scan: {isLoading ? 'Loading…' : lastScanDisplay}
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
            <thead className="bg-slate-100 dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2 text-left font-medium">Path</th>
                <th className="px-3 py-2 text-left font-medium">Checksum</th>
                <th className="px-3 py-2 text-left font-medium">Scanned</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {data?.records?.length ? (
                data.records.map((record) => (
                  <tr key={record.path}>
                    <td className="px-3 py-2 font-mono text-xs">{record.path}</td>
                    <td className="px-3 py-2 font-mono text-xs">{record.sha256}</td>
                    <td className="px-3 py-2 text-xs">
                      {new Date(record.scanned_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="px-3 py-4 text-center text-sm text-slate-500" colSpan={3}>
                    {isLoading || isFetching ? 'Loading records…' : 'No baselines recorded yet.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-lg font-semibold">Detected Drift</h2>
        {data?.drift?.length ? (
          <ul className="mt-3 space-y-3">
            {data.drift.map((item) => (
              <li key={`${item.path}-${item.reason}`} className="rounded-md border border-amber-400 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-500/60 dark:bg-amber-500/10 dark:text-amber-200">
                <div className="font-medium">{item.path}</div>
                <div className="mt-1 font-mono text-xs">
                  expected: {item.expected_sha ?? 'n/a'}
                </div>
                <div className="font-mono text-xs">
                  observed: {item.observed_sha ?? 'missing'}
                </div>
                <div className="mt-1 text-xs uppercase tracking-wide">{item.reason}</div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            {isLoading || isFetching ? 'Evaluating drift…' : 'No drift detected in the latest scan.'}
          </p>
        )}
      </section>
    </div>
  );
};

export default SecurityHygienePage;
