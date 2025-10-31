import { useQuery } from '@tanstack/react-query';

const fetchStatus = async () => {
  return {
    checks: [
      { name: 'database', status: 'OK' },
      { name: 'qdrant', status: 'OK' },
      { name: 'celery', status: 'WARN' }
    ],
  };
};

const DashboardPage = () => {
  const { data } = useQuery({ queryKey: ['ops-status'], queryFn: fetchStatus });

  return (
    <div className="space-y-4 p-6">
      <h1 className="text-2xl font-semibold">Ops Status</h1>
      <div className="space-y-2">
        {data?.checks.map((check) => (
          <div key={check.name} className="flex items-center justify-between rounded border p-3">
            <span>{check.name}</span>
            <span className={check.status === 'OK' ? 'text-emerald-600' : 'text-amber-600'}>{check.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DashboardPage;
