import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import App from './App';
import './index.css';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './components/theme-provider';
import { Toaster } from './components/ui/toaster';
import { ToastProvider } from './components/ui/use-toast';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

async function prepareMocks() {
  if (import.meta.env.DEV) {
    const { worker } = await import('./mocks/browser');
    await worker.start({ onUnhandledRequest: 'bypass' });
  }
}

prepareMocks().finally(() => {
  ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <AuthProvider>
            <ThemeProvider defaultTheme="light" storageKey="client-portal-theme">
              <BrowserRouter>
                <App />
                <Toaster />
              </BrowserRouter>
            </ThemeProvider>
          </AuthProvider>
        </ToastProvider>
      </QueryClientProvider>
    </React.StrictMode>,
  );
});
