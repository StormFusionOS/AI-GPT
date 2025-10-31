import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';

interface DomainHealthCardProps {
  domain: string;
  lastRun: string;
  robotsStatus: 'ok' | 'disallowed';
  openIssues: number;
}

export function DomainHealthCard({ domain, lastRun, robotsStatus, openIssues }: DomainHealthCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{domain}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm text-muted-foreground">
        <div className="flex items-center justify-between">
          <span>Last Run</span>
          <span>{formatDate(lastRun)}</span>
        </div>
        <div className="flex items-center justify-between">
          <span>Robots</span>
          <Badge variant={robotsStatus === 'ok' ? 'success' : 'destructive'}>
            {robotsStatus === 'ok' ? 'OK' : 'Disallowed'}
          </Badge>
        </div>
        <div className="flex items-center justify-between">
          <span>Open Issues</span>
          <Badge variant={openIssues > 0 ? 'warning' : 'success'}>{openIssues}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}
