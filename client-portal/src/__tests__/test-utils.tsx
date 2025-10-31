import { ReactElement } from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, type RenderOptions } from '@testing-library/react';

import { AuthProvider } from '../contexts/AuthContext';
import { ThemeProvider } from '../components/theme-provider';
import { ToastProvider } from '../components/ui/use-toast';

interface RenderProps {
  route?: string;
}

export function renderWithProviders(ui: ReactElement, { route = '/' }: RenderProps = {}, options?: RenderOptions) {
  const queryClient = new QueryClient();
  window.history.pushState({}, 'Test page', route);

  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AuthProvider>
          <ThemeProvider>
            <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
          </ThemeProvider>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>,
    options,
  );
}

export function renderWithRouter(ui: ReactElement, { route = '/' }: RenderProps = {}) {
  const queryClient = new QueryClient();

  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AuthProvider>
          <ThemeProvider>
            <MemoryRouter initialEntries={[route]}>
              <Routes>
                <Route path="*" element={ui} />
              </Routes>
            </MemoryRouter>
          </ThemeProvider>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>,
  );
}
