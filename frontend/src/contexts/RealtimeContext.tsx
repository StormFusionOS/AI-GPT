import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

import { useAuth } from './AuthContext';

export type RealtimeEventType = 'message.new' | 'lead.created' | 'lead.updated' | 'notification';

export interface RealtimeEvent<TPayload = unknown> {
  type: RealtimeEventType;
  payload: TPayload;
  receivedAt: string;
}

interface RealtimeContextValue {
  status: 'disconnected' | 'connecting' | 'connected';
  subscribe: (listener: (event: RealtimeEvent) => void) => () => void;
  emitLocal: (event: RealtimeEvent) => void;
}

const RealtimeContext = createContext<RealtimeContextValue | undefined>(undefined);

const WS_RECONNECT_INTERVAL = 5000;

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  const listeners = useRef(new Set<(event: RealtimeEvent) => void>());
  const websocketRef = useRef<WebSocket | null>(null);

  const broadcast = useCallback((event: RealtimeEvent) => {
    listeners.current.forEach((listener) => listener(event));
  }, []);

  useEffect(() => {
    if (!token) {
      websocketRef.current?.close();
      websocketRef.current = null;
      setStatus('disconnected');
      return;
    }

    let shouldReconnect = true;
    const wsUrl = resolveWebSocketUrl(token);

    const connect = () => {
      try {
        setStatus('connecting');
        const socket = new WebSocket(wsUrl);
        websocketRef.current = socket;

        socket.onopen = () => {
          setStatus('connected');
        };

        socket.onmessage = (message) => {
          try {
            const parsed = JSON.parse(message.data) as RealtimeEvent;
            broadcast({ ...parsed, receivedAt: new Date().toISOString() });
          } catch (error) {
            console.warn('Failed to parse realtime payload', error);
          }
        };

        socket.onclose = () => {
          setStatus('disconnected');
          websocketRef.current = null;
          if (shouldReconnect) {
            setTimeout(connect, WS_RECONNECT_INTERVAL);
          }
        };

        socket.onerror = () => {
          socket.close();
        };
      } catch (error) {
        console.error('Realtime connection error', error);
        setStatus('disconnected');
      }
    };

    connect();

    return () => {
      shouldReconnect = false;
      websocketRef.current?.close();
      websocketRef.current = null;
    };
  }, [broadcast, token]);

  const subscribe = useCallback((listener: (event: RealtimeEvent) => void) => {
    listeners.current.add(listener);
    return () => {
      listeners.current.delete(listener);
    };
  }, []);

  const emitLocal = useCallback(
    (event: RealtimeEvent) => {
      broadcast(event);
      if (websocketRef.current?.readyState === WebSocket.OPEN) {
        try {
          websocketRef.current.send(JSON.stringify(event));
        } catch (error) {
          console.warn('Failed to send realtime event', error);
        }
      }
    },
    [broadcast]
  );

  const value = useMemo(
    () => ({
      status,
      subscribe,
      emitLocal
    }),
    [emitLocal, status, subscribe]
  );

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error('useRealtime must be used within a RealtimeProvider');
  }
  return context;
}

function resolveWebSocketUrl(token: string) {
  const envUrl = import.meta.env.VITE_WS_URL as string | undefined;
  if (envUrl) {
    return `${envUrl}?token=${token}`;
  }
  const { location } = window;
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${location.host}/ws?token=${token}`;
}
