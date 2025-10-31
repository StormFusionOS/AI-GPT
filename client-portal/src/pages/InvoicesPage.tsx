import { useQuery } from '@tanstack/react-query';
import { Download, FileText } from 'lucide-react';

import { fetchInvoices } from '../services/api';
import type { Invoice } from '../types';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { useToast } from '../components/ui/use-toast';

const dateFormatter = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' });

export function InvoicesPage() {
  const { push } = useToast();
  const { data, isLoading } = useQuery<Invoice[]>({ queryKey: ['invoices'], queryFn: fetchInvoices });

  if (isLoading || !data) {
    return <div className="text-sm text-slate-500">Loading invoices...</div>;
  }

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Invoices & Payments</h2>
        <p className="text-sm text-slate-500">Review your billing history and download statements.</p>
      </header>
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Invoice</th>
              <th className="px-4 py-3">Amount</th>
              <th className="px-4 py-3">Issued</th>
              <th className="px-4 py-3">Due</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3" aria-label="actions" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {data.map((invoice) => (
              <tr key={invoice.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-800">{invoice.description ?? invoice.id}</td>
                <td className="px-4 py-3 text-slate-500">
                  {invoice.currency} {invoice.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </td>
                <td className="px-4 py-3 text-slate-500">{dateFormatter.format(new Date(invoice.issued_at))}</td>
                <td className="px-4 py-3 text-slate-500">{dateFormatter.format(new Date(invoice.due_date))}</td>
                <td className="px-4 py-3">
                  <Badge
                    variant={
                      invoice.status === 'paid'
                        ? 'success'
                        : invoice.status === 'overdue'
                        ? 'danger'
                        : 'warning'
                    }
                  >
                    {invoice.status}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-right">
                  {invoice.pdf_url ? (
                    <a
                      href={invoice.pdf_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-sm text-brand hover:underline"
                    >
                      <Download className="h-4 w-4" /> Download
                    </a>
                  ) : (
                    <span className="text-xs text-slate-400">Contact support</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-700">Need help with payments?</h3>
        <p className="mt-1 text-sm text-slate-500">
          Our billing team can enable online payments or set up ACH/credit card auto-pay.
        </p>
        <Button
          variant="secondary"
          className="mt-4"
          onClick={() =>
            push({
              title: 'Billing request sent',
              description: 'Our team will reach out within one business day.',
              variant: 'success',
            })
          }
        >
          <FileText className="mr-2 h-4 w-4" /> Contact billing team
        </Button>
      </div>
    </div>
  );
}
