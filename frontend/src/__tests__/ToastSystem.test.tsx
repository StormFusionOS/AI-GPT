import { describe, expect, it } from 'vitest';
import userEvent from '@testing-library/user-event';
import { screen } from '@testing-library/react';

import { useToast } from '@/components/ui/use-toast';
import { renderWithProviders } from './test-utils';

function ToastHarness() {
  const { toast } = useToast();
  return (
    <button
      type="button"
      onClick={() => toast({ title: 'Saved', description: 'Configuration updated successfully.' })}
    >
      Trigger Toast
    </button>
  );
}

describe('Toast system', () => {
  it('renders a toast notification when triggered', async () => {
    renderWithProviders(<ToastHarness />);

    await userEvent.click(screen.getByRole('button', { name: /trigger toast/i }));

    expect(await screen.findByText(/configuration updated successfully/i)).toBeInTheDocument();
  });
});
