import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { fetchQuotes, saveQuote, type Quote } from '@/services/api';

const STATUS_COLORS: Record<Quote['status'], string> = {
  draft: 'bg-slate-500/10 text-slate-500',
  sent: 'bg-blue-500/10 text-blue-500',
  accepted: 'bg-emerald-500/10 text-emerald-500',
  paid: 'bg-amber-500/10 text-amber-500'
};

export function QuotesPage() {
  const queryClient = useQueryClient();
  const { data: quotes } = useQuery({ queryKey: ['quotes'], queryFn: fetchQuotes });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [activeQuote, setActiveQuote] = useState<Quote | null>(null);
  const [notes, setNotes] = useState('');

  const mutation = useMutation({
    mutationFn: (quote: Quote) => saveQuote(quote),
    onSuccess: (quote) => {
      queryClient.setQueryData<Quote[]>(['quotes'], (prev) => {
        if (!prev) return [quote];
        const exists = prev.findIndex((item) => item.id === quote.id);
        if (exists >= 0) {
          const next = [...prev];
          next[exists] = quote;
          return next;
        }
        return [...prev, quote];
      });
      setDialogOpen(false);
      setActiveQuote(null);
      setNotes('');
    }
  });

  const totalPending = useMemo(() => quotes?.filter((quote) => quote.status !== 'paid').reduce((sum, quote) => sum + quote.total, 0) ?? 0, [quotes]);

  const openDialog = (quote?: Quote) => {
    setActiveQuote(
      quote ?? {
        id: `quote-${Date.now()}`,
        contactName: '',
        status: 'draft',
        total: 0,
        issuedAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
    );
    setDialogOpen(true);
  };

  const handleSave = () => {
    if (!activeQuote) return;
    mutation.mutate({ ...activeQuote, updatedAt: new Date().toISOString() });
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Quotes & invoices</h1>
          <p className="text-sm text-muted-foreground">Track proposals, sent quotes, and payment status.</p>
        </div>
        <Button onClick={() => openDialog()}>
          <Plus className="mr-2 h-4 w-4" /> New quote
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Outstanding</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">${totalPending.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground">Awaiting acceptance or payment</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Drafts</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{quotes?.filter((quote) => quote.status === 'draft').length ?? 0}</p>
            <p className="text-xs text-muted-foreground">Ready for review before sending</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Paid</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{quotes?.filter((quote) => quote.status === 'paid').length ?? 0}</p>
            <p className="text-xs text-muted-foreground">Closed out this month</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="text-base">Quotes</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Contact</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Issued</TableHead>
                <TableHead>Last updated</TableHead>
                <TableHead className="text-right">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {quotes?.map((quote) => (
                <TableRow key={quote.id} className="cursor-pointer" onClick={() => openDialog(quote)}>
                  <TableCell className="font-medium text-foreground">{quote.contactName || 'Untitled quote'}</TableCell>
                  <TableCell>
                    <Badge className={STATUS_COLORS[quote.status]}> {quote.status}</Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{new Date(quote.issuedAt).toLocaleDateString()}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{new Date(quote.updatedAt).toLocaleDateString()}</TableCell>
                  <TableCell className="text-right font-semibold">${quote.total.toLocaleString()}</TableCell>
                </TableRow>
              ))}
              {!quotes?.length && (
                <TableRow>
                  <TableCell colSpan={5} className="py-8 text-center text-sm text-muted-foreground">
                    No quotes available.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{activeQuote?.contactName ? 'Edit quote' : 'Create quote'}</DialogTitle>
            <DialogDescription>Prepare proposals for leads and share via email or PDF.</DialogDescription>
          </DialogHeader>
          {activeQuote && (
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium">Contact</label>
                <Input
                  value={activeQuote.contactName}
                  onChange={(event) => setActiveQuote((prev) => (prev ? { ...prev, contactName: event.target.value } : prev))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Status</label>
                <Input
                  value={activeQuote.status}
                  onChange={(event) =>
                    setActiveQuote((prev) => (prev ? { ...prev, status: event.target.value as Quote['status'] } : prev))
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Total</label>
                <Input
                  type="number"
                  value={activeQuote.total}
                  onChange={(event) =>
                    setActiveQuote((prev) => (prev ? { ...prev, total: Number(event.target.value) } : prev))
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Notes</label>
                <Textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={4} />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={mutation.isPending || !activeQuote?.contactName}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
