import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navigate, Route, Routes } from 'react-router-dom';

import AlertsPage from '../pages/AlertsPage';
import DashboardPage from '../pages/DashboardPage';
import LoginPage from '../pages/LoginPage';
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
      </Route>
    </Routes>
  </QueryClientProvider>
);

export default App;
