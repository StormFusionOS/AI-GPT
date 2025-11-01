const alerts = [
  { id: '1', level: 'CRITICAL', message: 'Backup overdue' },
  { id: '2', level: 'WARN', message: 'Plugin update required' }
];

const AlertsPage = () => (
  <div className="space-y-4 p-6">
    <h1 className="text-2xl font-semibold">Active Alerts</h1>
    <ul className="space-y-2">
      {alerts.map((alert) => (
        <li key={alert.id} className="rounded border p-3">
          <p className="text-sm text-slate-500">{alert.level}</p>
          <p className="font-medium">{alert.message}</p>
        </li>
      ))}
    </ul>
  </div>
);

export default AlertsPage;
