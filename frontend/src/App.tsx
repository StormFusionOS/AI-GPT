import { useQuery } from '@tanstack/react-query';
import { Button } from './components/ui/button';
import { ThemeToggle } from './components/theme-toggle';
import { fetchHealth } from './lib/api';

function App() {
  const { data, refetch, isFetching } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth
  });

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="container flex items-center justify-between py-6">
          <h1 className="text-2xl font-semibold">AI SEO Dashboard</h1>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Button onClick={() => refetch()} disabled={isFetching}>
              {isFetching ? 'Checking…' : 'Check API Health'}
            </Button>
          </div>
        </div>
      </header>
      <main className="container py-10">
        <section className="rounded-lg border bg-card p-6 shadow-sm">
          <h2 className="text-xl font-medium">Backend status</h2>
          <p className="mt-2 text-muted-foreground">
            {data?.status ?? 'Loading API status...'}
          </p>
        </section>
      </main>
    </div>
  );
}

export default App;
