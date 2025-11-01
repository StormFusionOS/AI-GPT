import { useQuery } from '@tanstack/react-query';

const fetchSummary = async () => {
  return { totalLeads: 12, wonLeads: 4, upcomingAppointments: 2 };
};

const DashboardPage = () => {
  const { data } = useQuery({ queryKey: ['dashboard-summary'], queryFn: fetchSummary });

  return (
    <div className="space-y-4 p-6">
      <h1 className="text-2xl font-semibold">Sales Dashboard</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded border p-4 shadow">
          <p className="text-sm text-slate-500">Total Leads</p>
          <p className="text-2xl font-bold">{data?.totalLeads ?? 0}</p>
        </div>
        <div className="rounded border p-4 shadow">
          <p className="text-sm text-slate-500">Won Leads</p>
          <p className="text-2xl font-bold">{data?.wonLeads ?? 0}</p>
        </div>
        <div className="rounded border p-4 shadow">
          <p className="text-sm text-slate-500">Upcoming Appointments</p>
          <p className="text-2xl font-bold">{data?.upcomingAppointments ?? 0}</p>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
