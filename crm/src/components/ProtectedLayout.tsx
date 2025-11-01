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

  const links = [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/inbox', label: 'Inbox' },
    { to: '/leads', label: 'Leads' },
  ];

  return (
    <div className="flex min-h-screen bg-slate-100">
      <aside className="hidden w-56 flex-shrink-0 border-r bg-white p-6 md:block">
        <h1 className="mb-6 text-xl font-semibold text-slate-900">CRM Console</h1>
        <nav className="space-y-3">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `block rounded px-3 py-2 text-sm font-medium ${
                  isActive ? 'bg-emerald-500 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
};

export default ProtectedLayout;
