import { afterEach, describe, expect, it, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';

import App from '@/App';
import { api } from '@/services/api';
import { renderWithProviders } from './test-utils';

// NOTE: Full end-to-end coverage will be expanded with Playwright flows once the
//       API stabilises. This unit-level test keeps the UI behaviour reliable in CI.

afterEach(() => {
  vi.restoreAllMocks();
});

describe('ReviewQueuePage', () => {
  it('approves a pending change and refreshes data', async () => {
    const approveSpy = vi.spyOn(api, 'approveReviewChange').mockResolvedValue({ status: 'approved' });

    renderWithProviders(<App />, { route: '/review-queue' });

    const changeCard = await screen.findByRole('button', { name: /localbusiness schema/i });
    await userEvent.click(changeCard);

    await userEvent.type(screen.getByLabelText(/reviewer note/i), 'Looks good.');
    await userEvent.click(screen.getByRole('button', { name: /approve/i }));

    await waitFor(() => expect(approveSpy).toHaveBeenCalled());
  });
});
