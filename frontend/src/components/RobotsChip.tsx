import { Badge } from '@/components/ui/badge';

interface RobotsChipProps {
  status: 'ok' | 'disallowed';
}

export function RobotsChip({ status }: RobotsChipProps) {
  return <Badge variant={status === 'ok' ? 'success' : 'destructive'}>{status === 'ok' ? 'OK' : 'Disallowed'}</Badge>;
}
