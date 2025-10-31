import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface KpiCardProps {
  label: string;
  value: string | number;
  description?: string;
  trend?: string;
}

export function KpiCard({ label, value, description, trend }: KpiCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl font-bold">{value}</CardTitle>
      </CardHeader>
      {(description || trend) && (
        <CardContent className="text-sm text-muted-foreground">
          {description}
          {trend && <div className="mt-1 text-xs text-emerald-500">{trend}</div>}
        </CardContent>
      )}
    </Card>
  );
}
