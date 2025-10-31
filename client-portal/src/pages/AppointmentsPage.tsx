import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarClock, Clock } from 'lucide-react';
import { useState } from 'react';

import { fetchAppointments, submitReschedule } from '../services/api';
import type { Appointment } from '../types';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { useToast } from '../components/ui/use-toast';

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
});

export function AppointmentsPage() {
  const queryClient = useQueryClient();
  const { push } = useToast();
  const { data, isLoading } = useQuery<Appointment[]>({
    queryKey: ['appointments'],
    queryFn: fetchAppointments,
  });
  const [activeAppointment, setActiveAppointment] = useState<Appointment | null>(null);
  const [request, setRequest] = useState({ requested_start: '', message: '' });

  const reschedule = useMutation({
    mutationFn: (payload: { appointmentId: string; requested_start: string; message: string }) =>
      submitReschedule(payload.appointmentId, {
        requested_start: payload.requested_start,
        message: payload.message,
      }),
    onSuccess: () => {
      push({
        title: 'Reschedule request sent',
        description: 'We will confirm the new time shortly.',
        variant: 'success',
      });
      setActiveAppointment(null);
      setRequest({ requested_start: '', message: '' });
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
    },
    onError: () => {
      push({ title: 'Unable to submit request', description: 'Please try again later.', variant: 'destructive' });
    },
  });

  if (isLoading || !data) {
    return <div className="text-sm text-slate-500">Loading appointments...</div>;
  }

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Appointments</h2>
        <p className="text-sm text-slate-500">View upcoming and previous meetings with our team.</p>
      </header>
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">When</th>
              <th className="px-4 py-3">Staff</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3" aria-label="actions" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {data.map((appointment) => (
              <tr key={appointment.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-800">{appointment.title}</td>
                <td className="px-4 py-3 text-slate-500">
                  {dateFormatter.format(new Date(appointment.start))}
                  <div className="text-xs text-slate-400">Duration ~{formatDuration(appointment)}</div>
                </td>
                <td className="px-4 py-3 text-slate-500">{appointment.staff_member ?? 'TBD'}</td>
                <td className="px-4 py-3">
                  <Badge
                    variant={
                      appointment.status === 'scheduled'
                        ? 'success'
                        : appointment.status === 'completed'
                        ? 'default'
                        : 'warning'
                    }
                  >
                    {appointment.status}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-right">
                  {appointment.status === 'scheduled' ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setActiveAppointment(appointment);
                        setRequest({ requested_start: appointment.start.slice(0, 16), message: '' });
                      }}
                    >
                      Request reschedule
                    </Button>
                  ) : (
                    <span className="text-xs text-slate-400">Completed</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {activeAppointment && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <CalendarClock className="h-4 w-4" /> Request new time for {activeAppointment.title}
          </div>
          <form
            className="mt-4 space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              reschedule.mutate({
                appointmentId: activeAppointment.id,
                requested_start: request.requested_start,
                message: request.message,
              });
            }}
          >
            <div className="grid gap-2 md:grid-cols-2">
              <div className="space-y-1">
                <Label htmlFor="requested_start">Preferred time</Label>
                <Input
                  id="requested_start"
                  type="datetime-local"
                  required
                  value={request.requested_start}
                  onChange={(event) =>
                    setRequest((state) => ({ ...state, requested_start: event.target.value }))
                  }
                />
              </div>
              <div className="space-y-1">
                <Label>Current booking</Label>
                <div className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-500">
                  <Clock className="h-4 w-4" />
                  {dateFormatter.format(new Date(activeAppointment.start))}
                </div>
              </div>
            </div>
            <div className="space-y-1">
              <Label htmlFor="message">Share context</Label>
              <Textarea
                id="message"
                placeholder="Let us know why you need a different slot."
                value={request.message}
                required
                onChange={(event) => setRequest((state) => ({ ...state, message: event.target.value }))}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => setActiveAppointment(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={reschedule.isPending}>
                {reschedule.isPending ? 'Sending...' : 'Submit request'}
              </Button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function formatDuration(appointment: Appointment): string {
  const start = new Date(appointment.start).getTime();
  const end = new Date(appointment.end).getTime();
  const diffMinutes = Math.max(30, Math.round((end - start) / 60000));
  return `${diffMinutes} min`;
}
