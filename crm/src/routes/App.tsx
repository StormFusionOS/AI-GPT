import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navigate, Route, Routes } from 'react-router-dom';

import DashboardPage from '../pages/DashboardPage';
import InboxPage from '../pages/InboxPage';
import LeadsPage from '../pages/LeadsPage';
import LoginPage from '../pages/LoginPage';
import ProtectedLayout from '../components/ProtectedLayout';

const queryClient = new QueryClient();

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedLayout roles={["SALES", "SALES_MANAGER", "OWNER"]} />}
        >
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/inbox" element={<InboxPage />} />
          <Route path="/leads" element={<LeadsPage />} />
        </Route>
      </Routes>
    </QueryClientProvider>
  );
};

export default App;
