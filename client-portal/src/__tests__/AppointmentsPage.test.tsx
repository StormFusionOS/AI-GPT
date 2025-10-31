import { describe, it, expect, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';

import { AppointmentsPage } from '../pages/AppointmentsPage';
import { renderWithProviders } from './test-utils';

beforeEach(() => {
  window.localStorage.setItem(
    'client-portal-auth',
    JSON.stringify({
      token: 'mock-client-token-client-001',
      clientId: 'client-001',
      name: 'River City Clean Co.',
      primaryContact: 'Jordan Blake',
    }),
  );
});

describe('AppointmentsPage', () => {
  it('lists scheduled appointments', async () => {
    renderWithProviders(<AppointmentsPage />);

    const row = await screen.findByText(/Monthly SEO Strategy Review/i);
    expect(row).toBeInTheDocument();
  });
});
