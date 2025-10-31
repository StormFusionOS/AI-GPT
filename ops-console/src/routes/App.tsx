import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navigate, Route, Routes } from 'react-router-dom';

import AlertsPage from '../pages/AlertsPage';
import DashboardPage from '../pages/DashboardPage';
import LoginPage from '../pages/LoginPage';
import SystemHealthPage from '../pages/SystemHealth';
import SecurityHygienePage from '../pages/SecurityHygiene';
import BackupsPage from '../pages/BackupsPage';
import JobSchedulerPage from '../pages/JobScheduler';
import ProtectedLayout from '../components/ProtectedLayout';

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedLayout roles={["SEO_ENGINEER", "DEVOPS", "OWNER"]} />}
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/job-scheduler" element={<JobSchedulerPage />} />
        <Route path="/system-health" element={<SystemHealthPage />} />
        <Route path="/backups" element={<BackupsPage />} />
        <Route path="/security-hygiene" element={<SecurityHygienePage />} />
      </Route>
    </Routes>
  </QueryClientProvider>
);

export default App;
