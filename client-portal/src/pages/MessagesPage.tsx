import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Send, Mail, MessageSquareText, Phone } from 'lucide-react';
import { useState } from 'react';

import { fetchInteractions, sendMessage } from '../services/api';
import type { Interaction, MessageRequest } from '../types';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { useToast } from '../components/ui/use-toast';

const formatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
});

const channelIcon: Record<string, JSX.Element> = {
  email: <Mail className="h-4 w-4 text-slate-500" />,
  sms: <Phone className="h-4 w-4 text-slate-500" />,
  portal: <MessageSquareText className="h-4 w-4 text-slate-500" />,
};

export function MessagesPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery<Interaction[]>({ queryKey: ['interactions'], queryFn: fetchInteractions });
  const { push } = useToast();
  const [message, setMessage] = useState('');
  const [channel, setChannel] = useState<MessageRequest['channel']>('portal');

  const mutation = useMutation({
    mutationFn: (payload: MessageRequest) => sendMessage(payload),
    onSuccess: () => {
      push({ title: 'Message sent', description: 'We’ll be in touch shortly.', variant: 'success' });
      setMessage('');
      queryClient.invalidateQueries({ queryKey: ['interactions'] });
    },
    onError: () => {
      push({ title: 'Unable to send', description: 'Please try again later.', variant: 'destructive' });
    },
  });

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Messages</h2>
        <p className="text-sm text-slate-500">A timeline of conversations with the River City team.</p>
      </header>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-700">Send a message</h3>
        <p className="text-xs text-slate-500">Pick your preferred channel—we’ll notify your account team instantly.</p>
        <form
          className="mt-4 space-y-3"
          onSubmit={(event) => {
            event.preventDefault();
            mutation.mutate({ content: message, channel });
          }}
        >
          <div className="flex gap-2 text-xs">
            {(['portal', 'email', 'sms'] as const).map((value) => (
              <button
                key={value}
                type="button"
                className={`rounded-full px-3 py-1 font-medium ${
                  channel === value ? 'bg-brand text-white' : 'bg-slate-100 text-slate-600'
                }`}
                onClick={() => setChannel(value)}
              >
                {value.toUpperCase()}
              </button>
            ))}
          </div>
          <Textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            required
            placeholder="Share an update, ask a question, or request help."
          />
          <div className="flex justify-end">
            <Button type="submit" disabled={mutation.isPending}>
              <Send className="mr-2 h-4 w-4" /> {mutation.isPending ? 'Sending…' : 'Send message'}
            </Button>
          </div>
        </form>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <header className="border-b border-slate-200 px-6 py-4">
          <h3 className="text-sm font-semibold text-slate-700">Recent activity</h3>
        </header>
        <div className="max-h-[480px] space-y-0.5 overflow-y-auto px-6 py-4">
          {isLoading && <p className="text-sm text-slate-500">Loading messages…</p>}
          {!isLoading && data?.length === 0 && <p className="text-sm text-slate-500">No messages yet.</p>}
          {data?.map((interaction) => (
            <article key={interaction.id} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-2">
                  {channelIcon[interaction.channel] ?? <MessageSquareText className="h-4 w-4 text-slate-500" />}
                  {interaction.channel.toUpperCase()} · {interaction.direction}
                </span>
                <span>{formatter.format(new Date(interaction.occurred_at))}</span>
              </div>
              <h4 className="mt-2 text-sm font-semibold text-slate-800">{interaction.subject}</h4>
              <p className="mt-1 text-sm text-slate-600">{interaction.body_preview}</p>
              {interaction.staff_member && (
                <div className="mt-3 text-xs text-slate-500">Handled by {interaction.staff_member}</div>
              )}
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
