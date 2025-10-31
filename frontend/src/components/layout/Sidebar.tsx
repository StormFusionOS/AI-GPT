import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { SCRAPER_NAV_ITEMS } from '@/config/navigation';
import { Icon } from '@/components/icon';
import { ScrollArea } from '@/components/ui/scroll-area';

export function Sidebar() {
  return (
    <aside className="hidden h-screen w-64 border-r border-border bg-card text-sm md:flex">
      <div className="flex h-full w-full flex-col">
        <div className="flex items-center gap-2 border-b border-border px-6 py-4 text-lg font-semibold">
          <Icon name="layout-dashboard" className="h-5 w-5" />
          Scraper Console
        </div>
        <ScrollArea className="flex-1">
          <nav className="flex flex-col gap-1 p-4">
            <div className="px-2 pb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Scraper
            </div>
            {SCRAPER_NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground',
                    isActive && 'bg-accent text-accent-foreground',
                  )
                }
              >
                <Icon name={item.icon} className="h-4 w-4" />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </ScrollArea>
      </div>
    </aside>
  );
}
