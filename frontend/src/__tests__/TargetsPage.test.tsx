import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '@/App';
import { renderWithProviders } from './test-utils';

describe('TargetsPage', () => {
  it('filters targets and adds a new target via dialog', async () => {
    renderWithProviders(<App />, { route: '/targets' });

    expect(await screen.findByText('rivercityclean.com')).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText('Search domains or tags');
    await userEvent.type(searchInput, 'spotless');
    await waitFor(() => expect(screen.getByText('spotlessseattle.com')).toBeInTheDocument());

    await userEvent.clear(searchInput);

    await userEvent.click(screen.getByRole('button', { name: /add target/i }));

    const domainInput = await screen.findByLabelText(/domain/i);
    await userEvent.type(domainInput, 'newtarget.test');
    await userEvent.click(screen.getByRole('button', { name: /save target/i }));

    await waitFor(() => expect(screen.getByText('newtarget.test')).toBeInTheDocument());
  });
});
