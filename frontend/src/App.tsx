import { Route, Routes } from 'react-router-dom';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { DashboardPage } from '@/pages/Dashboard/DashboardPage';
import { TargetsPage } from '@/pages/Targets/TargetsPage';
import { SchedulesPage } from '@/pages/Schedules/SchedulesPage';
import { JobsPage } from '@/pages/Jobs/JobsPage';
import { ConfigPage } from '@/pages/Config/ConfigPage';
import { LogsPage } from '@/pages/Logs/LogsPage';
import { MediaBrowserPage } from '@/pages/MediaBrowser';
import { SnapshotsPage } from '@/pages/Snapshots/SnapshotsPage';
import { QuarantinePage } from '@/pages/Quarantine/QuarantinePage';
import { ProxiesPage } from '@/pages/Proxies/ProxiesPage';
import { SettingsPage } from '@/pages/Settings/SettingsPage';
import { SystemStatusPage } from '@/pages/SystemStatus/SystemStatusPage';
import { ReviewQueuePage } from '@/pages/ReviewQueue/ReviewQueuePage';
import { SEOAuditPage } from '@/pages/SEOAudit/SEOAuditPage';
import { DiffToolPage } from '@/pages/DevTools/DiffToolPage';

function App() {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="targets" element={<TargetsPage />} />
        <Route path="system-status" element={<SystemStatusPage />} />
        <Route path="review-queue" element={<ReviewQueuePage />} />
        <Route path="seo-audits" element={<SEOAuditPage />} />
        <Route path="dev-tools/diff" element={<DiffToolPage />} />
        <Route path="schedules" element={<SchedulesPage />} />
        <Route path="jobs" element={<JobsPage />} />
        <Route path="config" element={<ConfigPage />} />
        <Route path="logs" element={<LogsPage />} />
        <Route path="media" element={<MediaBrowserPage />} />
        <Route path="snapshots" element={<SnapshotsPage />} />
        <Route path="quarantine" element={<QuarantinePage />} />
        <Route path="proxies" element={<ProxiesPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}

export default App;
