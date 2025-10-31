import { Navigate, NavLink, Outlet, useLocation } from 'react-router-dom';

import { Role, useAuth } from '../lib/auth-context';

interface Props {
  roles: Role[];
}

const ProtectedLayout = ({ roles }: Props) => {
  const { token, role } = useAuth();
  const location = useLocation();

  if (!token || !role || !roles.includes(role)) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <aside className="hidden w-60 flex-col border-r border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900 md:flex">
        <h1 className="text-lg font-semibold">Ops Console</h1>
        <nav className="mt-6 space-y-2 text-sm">
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              `block rounded-md px-3 py-2 ${
                isActive ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900' : 'hover:bg-slate-100 dark:hover:bg-slate-800'
              }`
            }
          >
            Dashboard
          </NavLink>
          <NavLink
            to="/alerts"
            className={({ isActive }) =>
              `block rounded-md px-3 py-2 ${
                isActive ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900' : 'hover:bg-slate-100 dark:hover:bg-slate-800'
              }`
            }
          >
            Alerts
          </NavLink>
          <NavLink
            to="/system-health"
            className={({ isActive }) =>
              `block rounded-md px-3 py-2 ${
                isActive ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900' : 'hover:bg-slate-100 dark:hover:bg-slate-800'
              }`
            }
          >
            System Health
          </NavLink>
          <NavLink
            to="/backups"
            className={({ isActive }) =>
              `block rounded-md px-3 py-2 ${
                isActive ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900' : 'hover:bg-slate-100 dark:hover:bg-slate-800'
              }`
            }
          >
            Backups
          </NavLink>
          <NavLink
            to="/security-hygiene"
            className={({ isActive }) =>
              `block rounded-md px-3 py-2 ${
                isActive ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900' : 'hover:bg-slate-100 dark:hover:bg-slate-800'
              }`
            }
          >
            Security Hygiene
          </NavLink>
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
};

export default ProtectedLayout;
