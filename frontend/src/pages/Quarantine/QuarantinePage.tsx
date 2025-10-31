import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';
import { useToast } from '@/components/ui/use-toast';

export function QuarantinePage() {
  const { data = [], isLoading } = useQuery({ queryKey: ['quarantine'], queryFn: api.getQuarantine });
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const releaseMutation = useMutation({
    mutationFn: api.releaseDomain,
    onSuccess: () => {
      toast({ title: 'Domain released' });
      queryClient.invalidateQueries({ queryKey: ['quarantine'] });
    },
    onError: () => toast({ title: 'Failed to release domain', variant: 'destructive' }),
  });

  return (
    <div className="overflow-hidden rounded-md border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Domain</TableHead>
            <TableHead>Reason</TableHead>
            <TableHead>Until</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading && (
            <TableRow>
              <TableCell colSpan={4} className="text-center text-sm text-muted-foreground">
                Loading quarantine list…
              </TableCell>
            </TableRow>
          )}
          {!isLoading && data.length === 0 && (
            <TableRow>
              <TableCell colSpan={4} className="text-center text-sm text-muted-foreground">
                No domains in quarantine
              </TableCell>
            </TableRow>
          )}
          {data.map((entry) => (
            <TableRow key={entry.domain}>
              <TableCell className="font-medium">{entry.domain}</TableCell>
              <TableCell>
                <Badge variant="warning">{entry.reason.replace(/_/g, ' ')}</Badge>
              </TableCell>
              <TableCell>{formatDate(entry.until)}</TableCell>
              <TableCell className="flex justify-end gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => releaseMutation.mutate(entry.domain)}
                  disabled={releaseMutation.isPending}
                >
                  Release
                </Button>
                <Button size="sm" disabled>
                  Extend
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
