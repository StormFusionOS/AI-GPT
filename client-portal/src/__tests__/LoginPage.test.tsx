import { describe, it, expect, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { Routes, Route } from 'react-router-dom';

import { LoginPage } from '../pages/LoginPage';
import App from '../App';
import { renderWithRouter } from './test-utils';

beforeEach(() => {
  window.localStorage.clear();
});

describe('LoginPage', () => {
  it('authenticates and navigates to dashboard', async () => {
    renderWithRouter(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={<App />} />
      </Routes>,
      { route: '/login' },
    );

    await userEvent.type(screen.getByLabelText(/email/i), 'jordan@rivercityclean.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'client-portal-demo');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(screen.getByText(/welcome back/i)).toBeInTheDocument());
  });
});
