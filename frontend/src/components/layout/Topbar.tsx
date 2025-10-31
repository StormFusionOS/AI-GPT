import { Bell, HelpCircle, RefreshCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/theme-toggle';
import { useLocation, useNavigate } from 'react-router-dom';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { Input } from '@/components/ui/input';
import { useState } from 'react';

export function Topbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');

  function handleGlobalSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!search.trim()) return;
    navigate(`/logs?query=${encodeURIComponent(search.trim())}`);
  }

  return (
    <header className="flex h-16 w-full items-center justify-between border-b border-border bg-background px-4">
      <div className="flex flex-1 items-center gap-4">
        <Button variant="ghost" size="icon" aria-label="Refresh data" className="md:hidden">
          <RefreshCcw className="h-4 w-4" />
        </Button>
        <div className="hidden flex-col md:flex">
          <Breadcrumbs pathname={location.pathname} />
          <span className="text-xs text-muted-foreground">Monitor and operate scraper workloads</span>
        </div>
      </div>
      <form onSubmit={handleGlobalSearch} className="flex flex-1 justify-center px-4">
        <div className="hidden w-full max-w-sm md:block">
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search logs, jobs, domains"
            aria-label="Global search"
          />
        </div>
      </form>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" aria-label="Help">
          <HelpCircle className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Notifications">
          <Bell className="h-4 w-4" />
        </Button>
        <ThemeToggle />
      </div>
    </header>
  );
}
