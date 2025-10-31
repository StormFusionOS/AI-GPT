import { useQuery } from '@tanstack/react-query';
import { Calendar, CheckCircle2, MessageCircle, PhoneCall } from 'lucide-react';

import { fetchDashboard } from '../services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import type { DashboardSummary } from '../types';
import { useToast } from '../components/ui/use-toast';

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
});

export function DashboardPage() {
  const { push } = useToast();
  const { data, isLoading } = useQuery<DashboardSummary>({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    staleTime: 60_000,
  });

  if (isLoading || !data) {
    return <div className="text-sm text-slate-500">Loading your dashboard...</div>;
  }

  const nextAppointment = data.upcoming_appointments[0];
  const openInvoice = data.open_invoices[0];

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-2xl font-semibold text-slate-900">Welcome back, {data.primary_contact}</h1>
        <p className="mt-1 text-sm text-slate-500">
          Here’s the latest snapshot of your partnership with River City Clean Co.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Service Status</CardTitle>
            <CardDescription>Real-time update from your account manager</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-700">{data.service_status}</p>
            <Button
              className="mt-4"
              variant="outline"
              onClick={() =>
                push({
                  title: 'Status emailed',
                  description: 'We have sent the full summary to your inbox.',
                  variant: 'success',
                })
              }
            >
              Email me the latest report
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-4 w-4" /> Upcoming Appointment
            </CardTitle>
            <CardDescription>Keep an eye on your next touchpoint</CardDescription>
          </CardHeader>
          <CardContent>
            {nextAppointment ? (
              <div className="space-y-2">
                <p className="text-sm font-medium text-slate-800">{nextAppointment.title}</p>
                <p className="text-sm text-slate-500">
                  {dateFormatter.format(new Date(nextAppointment.start))} · {nextAppointment.location}
                </p>
                <Badge variant="success">{nextAppointment.status}</Badge>
              </div>
            ) : (
              <p className="text-sm text-slate-500">No upcoming appointments scheduled.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" /> Billing Summary
            </CardTitle>
            <CardDescription>Your current invoice status</CardDescription>
          </CardHeader>
          <CardContent>
            {openInvoice ? (
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-800">
                  {openInvoice.currency} {openInvoice.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </p>
                <p className="text-xs text-slate-500">Due {dateFormatter.format(new Date(openInvoice.due_date))}</p>
                <Badge variant={openInvoice.status === 'paid' ? 'success' : 'warning'}>{openInvoice.status}</Badge>
              </div>
            ) : (
              <p className="text-sm text-slate-500">You’re all caught up—no open invoices.</p>
            )}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Communications</CardTitle>
            <CardDescription>Latest messages from your River City team</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {data.recent_communications.map((interaction) => (
                <li key={interaction.id} className="rounded-lg border border-slate-200 p-3">
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span className="uppercase">{interaction.channel}</span>
                    <span>{dateFormatter.format(new Date(interaction.occurred_at))}</span>
                  </div>
                  <p className="mt-1 text-sm font-medium text-slate-800">{interaction.subject}</p>
                  <p className="mt-1 text-sm text-slate-500">{interaction.body_preview}</p>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Let us know how we can support you today</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              variant="secondary"
              className="w-full justify-start gap-2"
              onClick={() =>
                push({
                  title: 'Strategy session requested',
                  description: 'Your account manager will reach out within 1 business day.',
                  variant: 'success',
                })
              }
            >
              <PhoneCall className="h-4 w-4" /> Request a call
            </Button>
            <Button
              variant="secondary"
              className="w-full justify-start gap-2"
              onClick={() =>
                push({
                  title: 'Message composer opened',
                  description: 'Navigate to Messages to write to the team.',
                })
              }
            >
              <MessageCircle className="h-4 w-4" /> Send a message
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
