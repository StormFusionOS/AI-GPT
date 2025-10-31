import { Navigate, Outlet, Route, Routes, useLocation, type Location } from 'react-router-dom';

import { useAuth } from './contexts/AuthContext';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { AppointmentsPage } from './pages/AppointmentsPage';
import { MessagesPage } from './pages/MessagesPage';
import { InvoicesPage } from './pages/InvoicesPage';
import { ProfilePage } from './pages/ProfilePage';
import { LoginPage } from './pages/LoginPage';

function RequireAuth() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 text-slate-500">
        Loading portal...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}

function RedirectIfAuthenticated() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return null;
  }

  if (isAuthenticated) {
    const from = (location.state as { from?: Location })?.from?.pathname ?? '/';
    return <Navigate to={from} replace />;
  }

  return <Outlet />;
}

export default function App() {
  return (
    <Routes>
      <Route element={<RedirectIfAuthenticated />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>
      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="appointments" element={<AppointmentsPage />} />
          <Route path="messages" element={<MessagesPage />} />
          <Route path="invoices" element={<InvoicesPage />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
