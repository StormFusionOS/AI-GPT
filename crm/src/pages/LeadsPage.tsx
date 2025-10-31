const leads = [
  { id: '1', name: 'Acme Corp', status: 'NEW', value: '$5,000' },
  { id: '2', name: 'Globex', status: 'QUALIFIED', value: '$9,000' }
];

const LeadsPage = () => {
  return (
    <div className="space-y-4 p-6">
      <h1 className="text-2xl font-semibold">Leads</h1>
      <table className="min-w-full overflow-hidden rounded border">
        <thead className="bg-slate-100 text-left">
          <tr>
            <th className="px-4 py-2">Name</th>
            <th className="px-4 py-2">Status</th>
            <th className="px-4 py-2">Value</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr key={lead.id} className="border-t">
              <td className="px-4 py-2">{lead.name}</td>
              <td className="px-4 py-2">{lead.status}</td>
              <td className="px-4 py-2">{lead.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default LeadsPage;
