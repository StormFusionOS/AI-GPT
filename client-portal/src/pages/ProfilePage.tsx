import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { changePassword, fetchProfile, updateProfile } from '../services/api';
import type { Profile } from '../types';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Button } from '../components/ui/button';
import { useToast } from '../components/ui/use-toast';

export function ProfilePage() {
  const { push } = useToast();
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery<Profile>({ queryKey: ['profile'], queryFn: fetchProfile });
  const [password, setPassword] = useState('');

  const updateMutation = useMutation({
    mutationFn: (payload: Partial<Profile>) => updateProfile(payload),
    onSuccess: () => {
      push({ title: 'Profile updated', description: 'We saved your details.', variant: 'success' });
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
    onError: () => push({ title: 'Update failed', description: 'Please try again later.', variant: 'destructive' }),
  });

  const passwordMutation = useMutation({
    mutationFn: (newPassword: string) => changePassword({ new_password: newPassword }),
    onSuccess: () => {
      push({ title: 'Password updated', description: 'Your new password is active.', variant: 'success' });
      setPassword('');
    },
    onError: () => push({ title: 'Unable to update password', description: 'Please try again.', variant: 'destructive' }),
  });

  if (isLoading || !data) {
    return <div className="text-sm text-slate-500">Loading profile...</div>;
  }

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload: Partial<Profile> = {};
    formData.forEach((value, key) => {
      if (typeof value === 'string' && value.trim().length > 0) {
        payload[key as keyof Profile] = value.trim() as never;
      }
    });
    updateMutation.mutate(payload);
  };

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Profile & Preferences</h2>
        <p className="text-sm text-slate-500">Keep your contact info current so we can collaborate smoothly.</p>
      </header>

      <form className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm" onSubmit={handleSubmit}>
        <h3 className="text-sm font-semibold text-slate-700">Contact details</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="space-y-1">
            <Label htmlFor="name">Business name</Label>
            <Input id="name" name="name" defaultValue={data.name} required />
          </div>
          <div className="space-y-1">
            <Label htmlFor="primary_contact">Primary contact</Label>
            <Input id="primary_contact" name="primary_contact" defaultValue={data.primary_contact} required />
          </div>
          <div className="space-y-1">
            <Label htmlFor="email">Email</Label>
            <Input id="email" name="email" type="email" defaultValue={data.email} required />
          </div>
          <div className="space-y-1">
            <Label htmlFor="phone">Phone</Label>
            <Input id="phone" name="phone" defaultValue={data.phone ?? ''} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="address_line1">Address line 1</Label>
            <Input id="address_line1" name="address_line1" defaultValue={data.address_line1 ?? ''} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="address_line2">Address line 2</Label>
            <Input id="address_line2" name="address_line2" defaultValue={data.address_line2 ?? ''} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="city">City</Label>
            <Input id="city" name="city" defaultValue={data.city ?? ''} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="state_region">State/Region</Label>
            <Input id="state_region" name="state_region" defaultValue={data.state_region ?? ''} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="postal_code">Postal code</Label>
            <Input id="postal_code" name="postal_code" defaultValue={data.postal_code ?? ''} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="country">Country</Label>
            <Input id="country" name="country" defaultValue={data.country ?? ''} />
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <Button type="submit" disabled={updateMutation.isPending}>
            {updateMutation.isPending ? 'Saving…' : 'Save changes'}
          </Button>
        </div>
      </form>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-700">Change password</h3>
        <p className="text-xs text-slate-500">We recommend rotating your password every 90 days.</p>
        <form
          className="mt-4 flex flex-col gap-3 md:flex-row md:items-end"
          onSubmit={(event) => {
            event.preventDefault();
            passwordMutation.mutate(password);
          }}
        >
          <div className="flex-1 space-y-1">
            <Label htmlFor="new_password">New password</Label>
            <Input
              id="new_password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              required
            />
          </div>
          <Button type="submit" disabled={passwordMutation.isPending}>
            {passwordMutation.isPending ? 'Updating…' : 'Update password'}
          </Button>
        </form>
      </section>
    </div>
  );
}
