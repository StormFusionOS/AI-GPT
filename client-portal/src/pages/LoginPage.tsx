import { useState } from 'react';
import { useNavigate, useLocation, type Location } from 'react-router-dom';
import { useForm } from 'react-hook-form';

import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useToast } from '../components/ui/use-toast';

interface LoginFormValues {
  email: string;
  password: string;
}

export function LoginPage() {
  const { login } = useAuth();
  const { push } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [isSubmitting, setSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    defaultValues: { email: 'jordan@rivercityclean.com', password: 'client-portal-demo' },
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      setSubmitting(true);
      await login(values.email, values.password);
      const redirectTo = (location.state as { from?: Location })?.from?.pathname ?? '/';
      push({ title: 'Welcome!', description: 'You are now signed in.', variant: 'success' });
      navigate(redirectTo, { replace: true });
    } catch (error) {
      push({ title: 'Login failed', description: 'Please check your credentials.', variant: 'destructive' });
    } finally {
      setSubmitting(false);
    }
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-slate-100 px-4">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-lg">
        <h1 className="text-2xl font-semibold text-slate-900">Client Portal Login</h1>
        <p className="mt-2 text-sm text-slate-500">Access your projects, invoices, and conversations.</p>
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <div className="space-y-1">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" autoComplete="email" {...register('email', { required: true })} />
            {errors.email && <p className="text-xs text-red-600">Email is required.</p>}
          </div>
          <div className="space-y-1">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              {...register('password', { required: true })}
            />
            {errors.password && <p className="text-xs text-red-600">Password is required.</p>}
          </div>
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </Button>
        </form>
        <p className="mt-6 text-xs text-slate-400">
          Need help? Email <a href="mailto:support@rivercityclean.com">support@rivercityclean.com</a>
        </p>
      </div>
    </div>
  );
}
