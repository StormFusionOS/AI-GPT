import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';

import { LeadsKanban, type LeadSummary } from '@/components/LeadsKanban';
import { renderWithProviders } from './test-utils';

describe('LeadsKanban', () => {
  const sampleLeads: LeadSummary[] = [
    { id: 'lead-1', name: 'River City HQ', company: 'River City Clean', status: 'new', source: 'Website' },
    { id: 'lead-2', name: 'Spotless Seattle', company: 'Spotless', status: 'contacted', source: 'Referral' },
    { id: 'lead-3', name: 'Eco Offices', company: 'Eco Offices', status: 'won', value: 4500 },
  ];

  it('renders leads in the appropriate pipeline column', () => {
    renderWithProviders(<LeadsKanban leads={sampleLeads} />);

    expect(screen.getByRole('region', { name: /new column/i })).toHaveTextContent('River City HQ');
    expect(screen.getByRole('region', { name: /contacted column/i })).toHaveTextContent('Spotless Seattle');
    expect(screen.getByRole('region', { name: /won column/i })).toHaveTextContent('Eco Offices');
    expect(screen.getByRole('region', { name: /lost column/i })).toHaveTextContent('No leads in this stage');
  });
});
