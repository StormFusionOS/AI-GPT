import { Navigate, Route, Routes } from 'react-router-dom';

import { ProtectedRoute } from '@/components/ProtectedRoute';
import { DashboardLayout } from '@/layouts/DashboardLayout';
import { CalendarPage } from '@/pages/CalendarPage';
import { CampaignsPage } from '@/pages/CampaignsPage';
import { ContentPage } from '@/pages/ContentPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { InboxPage } from '@/pages/InboxPage';
import { LeadDetailPage } from '@/pages/LeadDetailPage';
import { LeadsPage } from '@/pages/LeadsPage';
import { LoginPage } from '@/pages/LoginPage';
import { QuotesPage } from '@/pages/QuotesPage';
import { ReviewQueuePage } from '@/pages/ReviewQueuePage';
import { SettingsPage } from '@/pages/SettingsPage';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="inbox" element={<InboxPage />} />
          <Route path="leads">
            <Route index element={<LeadsPage />} />
            <Route path=":id" element={<LeadDetailPage />} />
          </Route>
          <Route path="calendar" element={<CalendarPage />} />
          <Route path="quotes" element={<QuotesPage />} />
          <Route path="campaigns" element={<CampaignsPage />} />
          <Route element={<ProtectedRoute roles={['admin', 'manager', 'tech']} />}>
            <Route path="review-queue" element={<ReviewQueuePage />} />
          </Route>
          <Route element={<ProtectedRoute roles={['admin', 'manager']} />}>
            <Route path="content" element={<ContentPage />} />
          </Route>
          <Route element={<ProtectedRoute roles={['admin']} />}>
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
