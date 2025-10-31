import { ToastViewport } from './toast';
import { useToast } from './use-toast';

export function Toaster() {
  const { toasts, dismiss } = useToast();
  return <ToastViewport toasts={toasts} onDismiss={dismiss} />;
}
