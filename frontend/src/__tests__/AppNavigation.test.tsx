import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '@/App';
import { renderWithProviders } from './test-utils';

describe('App navigation', () => {
  it('navigates between dashboard and targets', async () => {
    renderWithProviders(<App />);

    expect(await screen.findByText(/recent events/i)).toBeInTheDocument();

    await userEvent.click(screen.getByRole('link', { name: /targets/i }));

    expect(await screen.findByRole('button', { name: /add target/i })).toBeInTheDocument();
  });
});
