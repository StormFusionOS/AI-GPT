import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { Calendar, FileText, Home, LogOut, Mail, Settings } from 'lucide-react';

import { useAuth } from '../../contexts/AuthContext';
import { ThemeToggle } from '../ThemeToggle';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';

const navigation = [
  { name: 'Dashboard', to: '/', icon: Home },
  { name: 'Appointments', to: '/appointments', icon: Calendar },
  { name: 'Messages', to: '/messages', icon: Mail },
  { name: 'Invoices', to: '/invoices', icon: FileText },
  { name: 'Profile', to: '/profile', icon: Settings },
];

function Breadcrumbs() {
  const location = useLocation();
  const segments = location.pathname.split('/').filter(Boolean);
  if (segments.length === 0) {
    return <span className="text-sm text-slate-500">Home</span>;
  }
  return (
    <div className="flex items-center gap-2 text-sm text-slate-500">
      <Link to="/" className="hover:text-slate-700">
        Home
      </Link>
      {segments.map((segment, index) => {
        const path = `/${segments.slice(0, index + 1).join('/')}`;
        const label = segment.charAt(0).toUpperCase() + segment.slice(1);
        return (
          <span key={path} className="flex items-center gap-2">
            <span aria-hidden="true">/</span>
            {index === segments.length - 1 ? (
              <span className="font-medium text-slate-700">{label}</span>
            ) : (
              <Link to={path} className="hover:text-slate-700">
                {label}
              </Link>
            )}
          </span>
        );
      })}
    </div>
  );
}

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen bg-slate-100">
      <aside className="hidden w-64 border-r border-slate-200 bg-white px-6 py-8 md:flex md:flex-col">
        <Link to="/" className="flex items-center gap-2 text-lg font-semibold text-brand">
          <span className="h-10 w-10 rounded-full bg-brand text-white grid place-items-center font-bold">RC</span>
          River City Client Portal
        </Link>
        <nav className="mt-10 flex flex-1 flex-col gap-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100',
                    isActive && 'bg-slate-900 text-white hover:bg-slate-900',
                  )
                }
              >
                <Icon className="h-4 w-4" />
                {item.name}
              </NavLink>
            );
          })}
        </nav>
        <div className="border-t border-slate-200 pt-4 text-sm text-slate-500">
          <p className="font-medium text-slate-700">{user?.name}</p>
          <p>{user?.primaryContact}</p>
        </div>
      </aside>
      <main className="flex w-full flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 shadow-sm">
          <div className="flex items-center gap-4">
            <button className="md:hidden" aria-label="Open navigation">
              <span className="block h-0.5 w-6 bg-slate-700" />
              <span className="mt-1 block h-0.5 w-6 bg-slate-700" />
              <span className="mt-1 block h-0.5 w-6 bg-slate-700" />
            </button>
            <Breadcrumbs />
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden text-sm text-slate-500 md:block">Welcome back, {user?.primaryContact}</span>
            <ThemeToggle />
            <Button variant="ghost" onClick={logout} className="text-slate-600" aria-label="Sign out">
              <LogOut className="mr-2 h-4 w-4" />
              <span className="hidden md:inline">Sign out</span>
            </Button>
          </div>
        </header>
        <div className="flex-1 px-4 py-6 md:px-10">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
