import { Badge } from '@/components/ui/badge';
import type { ReasonCode } from '@/types';

interface ReasonCodeBadgeProps {
  reason?: ReasonCode;
}

const COLOR_BY_REASON: Record<ReasonCode, 'destructive' | 'warning' | 'muted'> = {
  ROBOTS_DISALLOWED: 'warning',
  CAPTCHA_DETECTED: 'warning',
  RATE_LIMIT_429: 'warning',
  HARD_403: 'destructive',
  PARSER_EMPTY: 'muted',
  SCHEMA_MISSING: 'muted',
  NEEDS_MANUAL_URL: 'warning',
};

export function ReasonCodeBadge({ reason }: ReasonCodeBadgeProps) {
  if (!reason) return null;
  return <Badge variant={COLOR_BY_REASON[reason]}>{reason.replace(/_/g, ' ')}</Badge>;
}
