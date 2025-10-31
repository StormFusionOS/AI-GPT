import { render, screen } from '@testing-library/react';
import { JobStatusBadge } from '@/components/JobStatusBadge';

describe('JobStatusBadge', () => {
  it('renders variants for each status', () => {
    const statuses: Array<'running' | 'pending' | 'completed' | 'failed'> = [
      'running',
      'pending',
      'completed',
      'failed',
    ];

    statuses.forEach((status) => {
      render(<JobStatusBadge status={status} />);
      expect(screen.getByText(status.toUpperCase())).toBeInTheDocument();
    });
  });
});
