import { NavLink } from 'react-router-dom';

import { NAVIGATION_ITEMS } from '@/config/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';

export function Sidebar() {
  const { user } = useAuth();
  return (
    <aside className="flex h-full w-72 flex-col border-r border-border bg-background/95">
      <div className="flex items-center gap-2 border-b px-6 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
          <span className="text-lg font-semibold">AI</span>
        </div>
        <div>
          <p className="text-sm font-semibold leading-tight">AI Growth Studio</p>
          <p className="text-xs text-muted-foreground">Admin Console</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAVIGATION_ITEMS.filter((item) => !item.roles || (user && item.roles.includes(user.role))).map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition hover:bg-muted/60 hover:text-foreground',
                isActive && 'bg-primary/10 text-primary'
              )
            }
            end={item.path === '/'}
          >
            <item.icon className="h-4 w-4" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="border-t px-6 py-4 text-xs text-muted-foreground">
        <p className="font-medium text-foreground">Need help?</p>
        <p>docs.ai-growth-studio.com</p>
      </div>
    </aside>
  );
}
