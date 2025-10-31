import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { CalendarPlus, StickyNote, Send } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useAuth } from '@/contexts/AuthContext';
import { createAppointment, fetchLeadDetail, logInteraction, type LeadDetail } from '@/services/api';

export function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { data: lead } = useQuery({ queryKey: ['lead', id], queryFn: () => fetchLeadDetail(id!), enabled: Boolean(id) });
  const { user } = useAuth();
  const [interactionOpen, setInteractionOpen] = useState(false);
  const [appointmentOpen, setAppointmentOpen] = useState(false);
  const [interactionContent, setInteractionContent] = useState('');
  const [interactionChannel, setInteractionChannel] = useState('Email');
  const [appointmentForm, setAppointmentForm] = useState({ title: '', start: '', location: '' });

  const interactionMutation = useMutation({
    mutationFn: () => logInteraction(id!, { type: 'note', channel: interactionChannel, content: interactionContent }),
    onSuccess: (interaction) => {
      queryClient.setQueryData<LeadDetail>(['lead', id], (prev) =>
        prev ? { ...prev, interactions: [interaction, ...prev.interactions] } : prev
      );
      setInteractionContent('');
      setInteractionOpen(false);
    }
  });

  const appointmentMutation = useMutation({
    mutationFn: () =>
      createAppointment({
        contactId: lead!.id,
        title: appointmentForm.title,
        start: appointmentForm.start,
        end: appointmentForm.start,
        location: appointmentForm.location,
        status: 'scheduled',
        owner: user?.name ?? 'Team'
      }),
    onSuccess: (appointment) => {
      queryClient.setQueryData<LeadDetail>(['lead', id], (prev) =>
        prev ? { ...prev, appointments: [...prev.appointments, appointment] } : prev
      );
      setAppointmentForm({ title: '', start: '', location: '' });
      setAppointmentOpen(false);
    }
  });

  if (!lead) {
    return <p className="text-sm text-muted-foreground">Loading lead details…</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{lead.name}</h1>
          <p className="text-sm text-muted-foreground">
            {lead.email} · {lead.phone}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="outline" className="capitalize">
              {lead.status}
            </Badge>
            <span>Source · {lead.source}</span>
            {lead.campaign && <span>Campaign · {lead.campaign}</span>}
            <span>Owner · {lead.owner}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Dialog open={interactionOpen} onOpenChange={setInteractionOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <StickyNote className="mr-2 h-4 w-4" /> Log interaction
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Log interaction</DialogTitle>
                <DialogDescription>Keep the timeline up to date for shared context.</DialogDescription>
              </DialogHeader>
              <div className="space-y-3">
                <label className="text-sm font-medium">Channel</label>
                <Input value={interactionChannel} onChange={(event) => setInteractionChannel(event.target.value)} />
                <label className="text-sm font-medium">Notes</label>
                <Textarea value={interactionContent} onChange={(event) => setInteractionContent(event.target.value)} rows={4} />
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setInteractionOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={() => interactionMutation.mutate()} disabled={interactionMutation.isPending || !interactionContent.trim()}>
                  <Send className="mr-2 h-4 w-4" /> Save
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Dialog open={appointmentOpen} onOpenChange={setAppointmentOpen}>
            <DialogTrigger asChild>
              <Button>
                <CalendarPlus className="mr-2 h-4 w-4" /> Schedule appointment
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Schedule appointment</DialogTitle>
                <DialogDescription>Book time with {lead.name} and sync to the shared calendar.</DialogDescription>
              </DialogHeader>
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium">Title</label>
                  <Input value={appointmentForm.title} onChange={(event) => setAppointmentForm((prev) => ({ ...prev, title: event.target.value }))} />
                </div>
                <div>
                  <label className="text-sm font-medium">Start</label>
                  <Input type="datetime-local" value={appointmentForm.start} onChange={(event) => setAppointmentForm((prev) => ({ ...prev, start: event.target.value }))} />
                </div>
                <div>
                  <label className="text-sm font-medium">Location</label>
                  <Input value={appointmentForm.location} onChange={(event) => setAppointmentForm((prev) => ({ ...prev, location: event.target.value }))} />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setAppointmentOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={() => appointmentMutation.mutate()} disabled={appointmentMutation.isPending || !appointmentForm.title || !appointmentForm.start}>
                  <CalendarPlus className="mr-2 h-4 w-4" /> Save
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <section className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Timeline</CardTitle>
            <CardDescription>Calls, emails, and notes captured automatically.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {lead.interactions.map((interaction) => (
                <div key={interaction.id} className="relative rounded-lg border border-border/60 p-4">
                  <span className="absolute -left-2 top-4 h-3 w-3 rounded-full bg-primary" />
                  <div className="flex items-center justify-between text-sm">
                    <p className="font-medium capitalize">{interaction.type}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(interaction.occurredAt).toLocaleString()} · {interaction.channel}
                    </p>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{interaction.content}</p>
                </div>
              ))}
              {!lead.interactions.length && <p className="text-sm text-muted-foreground">No interactions yet.</p>}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Appointments</CardTitle>
            <CardDescription>Upcoming meetings with the prospect.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {lead.appointments.map((appointment) => (
              <div key={appointment.id} className="rounded-lg border border-border/60 p-3 text-sm">
                <p className="font-semibold">{appointment.title}</p>
                <p className="text-xs text-muted-foreground">
                  {new Date(appointment.start).toLocaleString()} · {appointment.location ?? 'TBD'}
                </p>
                <p className="text-xs text-muted-foreground">Owner · {appointment.owner}</p>
              </div>
            ))}
            {!lead.appointments.length && <p className="text-sm text-muted-foreground">No appointments scheduled.</p>}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
