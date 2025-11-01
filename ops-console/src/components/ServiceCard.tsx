import { formatDistanceToNow } from 'date-fns';

import type { ServiceHealth } from '../lib/api';

const statusColor: Record<ServiceHealth['status'], string> = {
  ok: 'bg-emerald-500',
  warn: 'bg-amber-500',
  down: 'bg-rose-500',
};

interface Props {
  service: ServiceHealth;
}

const ServiceCard = ({ service }: Props) => {
  const lastChecked = formatDistanceToNow(new Date(service.checked_at), { addSuffix: true });
  const description = service.details ? JSON.stringify(service.details) : 'No metadata';

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`h-2.5 w-2.5 rounded-full ${statusColor[service.status]}`} aria-hidden />
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{service.service}</h3>
        </div>
        <span className="text-xs text-slate-500 dark:text-slate-400">{lastChecked}</span>
      </div>
      <dl className="mt-3 space-y-1 text-xs text-slate-600 dark:text-slate-300">
        {service.latency_ms !== null && (
          <div className="flex justify-between">
            <dt>Latency</dt>
            <dd>{service.latency_ms} ms</dd>
          </div>
        )}
        <div className="flex justify-between">
          <dt>Details</dt>
          <dd className="max-w-xs truncate" title={description}>
            {description}
          </dd>
        </div>
      </dl>
    </div>
  );
};

export default ServiceCard;
