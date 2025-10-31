import { Badge } from '@/components/ui/badge';
import type { JobStatus } from '@/types';

interface JobStatusBadgeProps {
  status: JobStatus;
}

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  const variant =
    status === 'completed'
      ? 'success'
      : status === 'failed'
        ? 'destructive'
        : status === 'running'
          ? 'warning'
          : 'muted';
  return <Badge variant={variant}>{status.toUpperCase()}</Badge>;
}
