import { FormEvent, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

import { useAuth } from '../lib/auth-context';

const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (email === 'sales@example.com' && password === 'password123') {
      login('mock-token', 'SALES');
      const target = (location.state as { from?: Location })?.from?.pathname ?? '/dashboard';
      navigate(target);
    } else {
      setError('Invalid credentials');
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <form className="w-full max-w-sm space-y-4 rounded bg-white p-6 shadow" onSubmit={handleSubmit}>
        <h1 className="text-xl font-semibold">CRM Login</h1>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <div>
          <label className="block text-sm font-medium">Email</label>
          <input
            className="mt-1 w-full rounded border px-3 py-2"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Password</label>
          <input
            className="mt-1 w-full rounded border px-3 py-2"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        <button className="w-full rounded bg-blue-600 py-2 font-semibold text-white" type="submit">
          Sign in
        </button>
      </form>
    </main>
  );
};

export default LoginPage;
