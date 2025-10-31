import * as ToastPrimitive from '@radix-ui/react-toast';
import { cn } from '../../lib/utils';
import { type Toast } from './use-toast';

interface ToastViewportProps {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}

export function ToastViewport({ toasts, onDismiss }: ToastViewportProps) {
  return (
    <ToastPrimitive.Provider swipeDirection="right">
      {toasts.map((toast) => (
        <ToastPrimitive.Root
          key={toast.id}
          className={cn(
            'pointer-events-auto mt-2 w-96 rounded-md border border-slate-200 bg-white p-4 shadow-lg transition-all dark:border-slate-700 dark:bg-slate-900',
            toast.variant === 'destructive' && 'border-red-600 dark:border-red-500',
            toast.variant === 'success' && 'border-emerald-500',
          )}
          duration={toast.duration}
          onOpenChange={(open) => {
            if (!open) onDismiss(toast.id);
          }}
        >
          {toast.title && <ToastPrimitive.Title className="text-sm font-semibold">{toast.title}</ToastPrimitive.Title>}
          {toast.description && (
            <ToastPrimitive.Description className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              {toast.description}
            </ToastPrimitive.Description>
          )}
        </ToastPrimitive.Root>
      ))}
      <ToastPrimitive.Viewport className="fixed right-4 top-4 z-50 flex max-h-screen flex-col" />
    </ToastPrimitive.Provider>
  );
}
