import { format } from 'date-fns';

import type { TaskRun } from '../lib/api';

interface Props {
  tasks: TaskRun[];
}

const formatDate = (value?: string | null) => {
  if (!value) return '—';
  return format(new Date(value), 'yyyy-MM-dd HH:mm');
};

const TaskTable = ({ tasks }: Props) => (
  <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-800">
    <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
      <thead className="bg-slate-50 dark:bg-slate-800/40">
        <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          <th className="px-4 py-3">ID</th>
          <th className="px-4 py-3">Module</th>
          <th className="px-4 py-3">Task</th>
          <th className="px-4 py-3">Status</th>
          <th className="px-4 py-3">Queued</th>
          <th className="px-4 py-3">Started</th>
          <th className="px-4 py-3">Finished</th>
          <th className="px-4 py-3">Retries</th>
          <th className="px-4 py-3">Message</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-200 bg-white text-sm dark:divide-slate-800 dark:bg-slate-900">
        {tasks.map((task) => (
          <tr key={task.id} className="text-slate-700 dark:text-slate-200">
            <td className="px-4 py-2 font-mono text-xs">{task.id}</td>
            <td className="px-4 py-2 capitalize">{task.module}</td>
            <td className="px-4 py-2">{task.task}</td>
            <td className="px-4 py-2">{task.status}</td>
            <td className="px-4 py-2">{formatDate(task.queued_at)}</td>
            <td className="px-4 py-2">{formatDate(task.started_at)}</td>
            <td className="px-4 py-2">{formatDate(task.finished_at)}</td>
            <td className="px-4 py-2 text-center">{task.retries}</td>
            <td className="px-4 py-2 text-xs text-slate-500 dark:text-slate-400">{task.message ?? '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export default TaskTable;
