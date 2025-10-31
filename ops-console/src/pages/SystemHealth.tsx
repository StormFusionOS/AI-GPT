import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

import ServiceCard from '../components/ServiceCard';
import TaskTable from '../components/TaskTable';
import { fetchHealth, fetchTasks } from '../lib/api';
import { useAuth } from '../lib/auth-context';

const SystemHealthPage = () => {
  const { token } = useAuth();
  const { data: health } = useQuery({
    queryKey: ['orchestrator-health'],
    queryFn: () => fetchHealth(token ?? ''),
    enabled: Boolean(token),
    staleTime: 30_000,
  });

  const { data: tasks } = useQuery({
    queryKey: ['orchestrator-tasks'],
    queryFn: () => fetchTasks(token ?? '', { status: 'failed' }),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });

  const services = useMemo(() => health?.services ?? [], [health]);
  const taskItems = tasks?.items ?? [];

  return (
    <div className="space-y-8 px-6 py-4">
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">System Health</h1>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Observe infrastructure status and recent orchestrated jobs across AI, crawler, and publishing stacks.
        </p>
      </header>

      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          Services
        </h2>
        <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {services.map((service) => (
            <ServiceCard key={service.service} service={service} />
          ))}
          {services.length === 0 && (
            <div className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
              No health records yet.
            </div>
          )}
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Recent Tasks
          </h2>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Showing failed tasks first for quick remediation
          </span>
        </div>
        <div className="mt-3">
          <TaskTable tasks={taskItems} />
        </div>
      </section>
    </div>
  );
};

export default SystemHealthPage;
