import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ComponentType, SVGProps } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { PaperPlane, Phone, Mail as MailIcon, MessageSquareText } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { useAuth } from '@/contexts/AuthContext';
import { useRealtime } from '@/contexts/RealtimeContext';
import { useRealtimeSubscription } from '@/hooks/useRealtimeSubscription';
import { fetchInboxThreads, sendThreadMessage, type InboxMessage, type InboxThread } from '@/services/api';

const CHANNEL_ICONS: Record<string, ComponentType<SVGProps<SVGSVGElement>>> = {
  Email: MailIcon,
  'Twilio SMS': MessageSquareText,
  Voice: Phone
};

export function InboxPage() {
  const queryClient = useQueryClient();
  const { data: threads } = useQuery({ queryKey: ['inbox'], queryFn: fetchInboxThreads, refetchInterval: 30_000 });
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const { user } = useAuth();
  const { emitLocal } = useRealtime();

  const selectedThread = useMemo(() => threads?.find((thread) => thread.id === selectedThreadId), [selectedThreadId, threads]);

  useEffect(() => {
    if (!selectedThreadId && threads?.length) {
      setSelectedThreadId(threads[0].id);
    }
  }, [selectedThreadId, threads]);

  const mutation = useMutation({
    mutationFn: async (body: string) => {
      if (!selectedThreadId) throw new Error('No thread selected');
      const response = await sendThreadMessage(selectedThreadId, body);
      return response;
    },
    onSuccess: (newMessage) => {
      queryClient.setQueryData<InboxThread[]>(['inbox'], (prev) => {
        if (!prev) return prev;
        return prev.map((thread) =>
          thread.id === newMessage.threadId
            ? { ...thread, messages: [...thread.messages, newMessage], lastMessageAt: newMessage.sentAt, preview: newMessage.body }
            : thread
        );
      });
      emitLocal({ type: 'message.new', payload: newMessage, receivedAt: new Date().toISOString() });
    }
  });

  useRealtimeSubscription(
    useCallback(
      (event) => {
        if (event.type !== 'message.new') return;
        const incoming = event.payload as InboxMessage;
        queryClient.setQueryData<InboxThread[]>(['inbox'], (prev) => {
          if (!prev) return prev;
          const exists = prev.some((thread) => thread.id === incoming.threadId);
          if (!exists) {
            return [
              {
                id: incoming.threadId,
                contactId: incoming.threadId,
                contactName: incoming.sender.name,
                channel: 'Twilio SMS',
                lastMessageAt: incoming.sentAt,
                unreadCount: 1,
                preview: incoming.body,
                messages: [incoming]
              },
              ...prev
            ];
          }
          return prev.map((thread) =>
            thread.id === incoming.threadId
              ? {
                  ...thread,
                  messages: [...thread.messages, incoming],
                  lastMessageAt: incoming.sentAt,
                  preview: incoming.body,
                  unreadCount: thread.id === selectedThreadId ? thread.unreadCount : thread.unreadCount + 1
                }
              : thread
          );
        });
      },
      [queryClient, selectedThreadId]
    )
  );

  const handleSend = async () => {
    if (!message.trim()) return;
    await mutation.mutateAsync(message.trim());
    setMessage('');
  };

  return (
    <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
      <Card className="h-[calc(100vh-7rem)] overflow-hidden">
        <CardHeader>
          <CardTitle>Conversations</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[calc(100vh-10rem)]">
            <div className="space-y-1 p-2">
              {threads?.map((thread) => {
                const Icon = CHANNEL_ICONS[thread.channel] ?? MessageSquareText;
                const isActive = thread.id === selectedThreadId;
                return (
                  <button
                    key={thread.id}
                    className={`w-full rounded-md border px-3 py-2 text-left transition ${
                      isActive ? 'border-primary bg-primary/10' : 'border-transparent hover:border-border hover:bg-muted'
                    }`}
                    onClick={() => setSelectedThreadId(thread.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4 text-muted-foreground" />
                        <p className="text-sm font-semibold">{thread.contactName}</p>
                      </div>
                      {thread.unreadCount > 0 && <Badge>{thread.unreadCount}</Badge>}
                    </div>
                    <p className="line-clamp-1 text-xs text-muted-foreground">{thread.preview}</p>
                    <p className="text-[10px] text-muted-foreground">
                      {new Date(thread.lastMessageAt).toLocaleString()}
                    </p>
                  </button>
                );
              })}
              {!threads?.length && <p className="p-4 text-center text-sm text-muted-foreground">No conversations yet.</p>}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      <Card className="h-[calc(100vh-7rem)]">
        <CardHeader className="border-b border-border/60">
          <CardTitle>{selectedThread?.contactName ?? 'Select a conversation'}</CardTitle>
        </CardHeader>
        <CardContent className="flex h-full flex-col p-0">
          <ScrollArea className="flex-1 px-6 py-4">
            <div className="space-y-4">
              {selectedThread?.messages.map((msg) => (
                <div key={msg.id} className="flex flex-col">
                  <span className="mb-1 text-xs text-muted-foreground">
                    {msg.sender.name} · {new Date(msg.sentAt).toLocaleTimeString()}
                  </span>
                  <div
                    className={`max-w-md rounded-lg border px-3 py-2 text-sm ${
                      msg.direction === 'outbound'
                        ? 'ml-auto border-primary bg-primary/10 text-primary'
                        : 'border-border bg-background'
                    }`}
                  >
                    {msg.body}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
          {selectedThread && (
            <div className="border-t border-border/60 p-4">
              <div className="flex items-end gap-3">
                <Textarea
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  placeholder={`Reply to ${selectedThread.contactName}`}
                  className="min-h-[90px]"
                />
                <Button onClick={handleSend} disabled={mutation.isPending}>
                  <PaperPlane className="mr-2 h-4 w-4" />
                  Send
                </Button>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Messages are delivered via {selectedThread.channel}. Signed in as {user?.name}.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
