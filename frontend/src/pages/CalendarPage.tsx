import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { addMonths, eachDayOfInterval, endOfMonth, endOfWeek, format, isSameDay, isSameMonth, startOfMonth, startOfWeek } from 'date-fns';
import { Calendar, ChevronLeft, ChevronRight, Plus } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useAuth } from '@/contexts/AuthContext';
import { createAppointment, fetchAppointments, type Appointment } from '@/services/api';

export function CalendarPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [referenceDate, setReferenceDate] = useState(() => new Date());
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ title: '', start: '', location: '', notes: '' });
  const { data: appointments } = useQuery({ queryKey: ['appointments'], queryFn: fetchAppointments, staleTime: 60_000 });

  const days = useMemo(() => {
    const start = startOfWeek(startOfMonth(referenceDate), { weekStartsOn: 0 });
    const end = endOfWeek(endOfMonth(referenceDate), { weekStartsOn: 0 });
    return eachDayOfInterval({ start, end });
  }, [referenceDate]);

  const mutation = useMutation({
    mutationFn: () =>
      createAppointment({
        contactId: 'contact-temp',
        title: form.title,
        start: form.start,
        end: form.start,
        location: form.location,
        status: 'scheduled',
        owner: user?.name ?? 'Team'
      }),
    onSuccess: (appointment) => {
      queryClient.setQueryData<Appointment[]>(['appointments'], (prev) => (prev ? [...prev, appointment] : [appointment]));
      setDialogOpen(false);
      setForm({ title: '', start: '', location: '', notes: '' });
    }
  });

  const appointmentsByDay = useMemo(() => {
    const map = new Map<string, Appointment[]>();
    (appointments ?? []).forEach((appointment) => {
      const dateKey = format(new Date(appointment.start), 'yyyy-MM-dd');
      map.set(dateKey, [...(map.get(dateKey) ?? []), appointment]);
    });
    return map;
  }, [appointments]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Calendar</h1>
          <p className="text-sm text-muted-foreground">Manage appointments and campaign milestones.</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" /> New appointment
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create appointment</DialogTitle>
              <DialogDescription>Track upcoming meetings across the team.</DialogDescription>
            </DialogHeader>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium">Title</label>
                <Input value={form.title} onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))} />
              </div>
              <div>
                <label className="text-sm font-medium">Date & time</label>
                <Input type="datetime-local" value={form.start} onChange={(event) => setForm((prev) => ({ ...prev, start: event.target.value }))} />
              </div>
              <div>
                <label className="text-sm font-medium">Location</label>
                <Input value={form.location} onChange={(event) => setForm((prev) => ({ ...prev, location: event.target.value }))} />
              </div>
              <div>
                <label className="text-sm font-medium">Notes</label>
                <Textarea value={form.notes} onChange={(event) => setForm((prev) => ({ ...prev, notes: event.target.value }))} rows={3} />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !form.title || !form.start}>
                Save
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="text-lg font-medium">{format(referenceDate, 'MMMM yyyy')}</CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={() => setReferenceDate((prev) => addMonths(prev, -1))}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={() => setReferenceDate(new Date())}>
              <Calendar className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={() => setReferenceDate((prev) => addMonths(prev, 1))}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-7 gap-2 text-xs font-medium uppercase text-muted-foreground">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
              <div key={day} className="p-2 text-center">
                {day}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-2">
            {days.map((day) => {
              const dateKey = format(day, 'yyyy-MM-dd');
              const dayAppointments = appointmentsByDay.get(dateKey) ?? [];
              return (
                <div
                  key={dateKey}
                  className={`min-h-[110px] rounded-lg border p-2 text-xs transition ${
                    isSameMonth(day, referenceDate) ? 'border-border bg-background' : 'border-dashed border-border/50 bg-muted/20'
                  } ${isSameDay(day, new Date()) ? 'ring-2 ring-primary' : ''}`}
                >
                  <div className="mb-1 flex items-center justify-between text-[11px] font-medium">
                    <span>{format(day, 'd')}</span>
                    {dayAppointments.length > 0 && (
                      <span className="rounded-full bg-primary/10 px-2 py-0.5 text-primary">{dayAppointments.length}</span>
                    )}
                  </div>
                  <ul className="space-y-1">
                    {dayAppointments.slice(0, 3).map((appointment) => (
                      <li key={appointment.id} className="truncate rounded border border-primary/40 bg-primary/5 px-2 py-1 text-[11px] text-primary">
                        {format(new Date(appointment.start), 'HH:mm')} · {appointment.title}
                      </li>
                    ))}
                    {dayAppointments.length > 3 && (
                      <li className="text-[11px] text-muted-foreground">+{dayAppointments.length - 3} more</li>
                    )}
                  </ul>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
