import * as React from 'react';
import { v4 as uuid } from 'uuid';

export type ToastVariant = 'default' | 'success' | 'destructive';

export interface Toast {
  id: string;
  title?: string;
  description?: string;
  duration?: number;
  variant?: ToastVariant;
}

interface ToastContextValue {
  toasts: Toast[];
  dismiss: (id: string) => void;
  push: (toast: Omit<Toast, 'id'>) => void;
}

const ToastContext = React.createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const dismiss = React.useCallback((id: string) => {
    setToasts((items) => items.filter((toast) => toast.id !== id));
  }, []);

  const push = React.useCallback((toast: Omit<Toast, 'id'>) => {
    const id = uuid();
    setToasts((items) => [...items, { id, duration: 4000, ...toast }]);
  }, []);

  const value = React.useMemo(() => ({ toasts, dismiss, push }), [toasts, dismiss, push]);

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
}

export function useToast() {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
}
