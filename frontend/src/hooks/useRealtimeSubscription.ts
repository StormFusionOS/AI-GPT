import { useEffect } from 'react';

import { RealtimeEvent, useRealtime } from '@/contexts/RealtimeContext';

export function useRealtimeSubscription(callback: (event: RealtimeEvent) => void) {
  const { subscribe } = useRealtime();

  useEffect(() => {
    return subscribe(callback);
  }, [callback, subscribe]);
}
