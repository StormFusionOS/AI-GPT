import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import type { ClientIdentity } from '../types';
import * as api from '../services/api';

interface AuthContextValue {
  user: ClientIdentity | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const STORAGE_KEY = 'client-portal-auth';

interface PersistedAuth {
  token: string;
  clientId: string;
  name: string;
  primaryContact: string;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<ClientIdentity | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);

  useEffect(() => {
    const storedRaw = window.localStorage.getItem(STORAGE_KEY);
    if (!storedRaw) {
      setLoading(false);
      return;
    }
    try {
      const parsed = JSON.parse(storedRaw) as PersistedAuth;
      const identity: ClientIdentity = {
        clientId: parsed.clientId,
        name: parsed.name,
        primaryContact: parsed.primaryContact,
        role: 'client',
      };
      setUser(identity);
      setToken(parsed.token);
      api.setAuthContext(parsed.token, parsed.clientId);
    } catch (error) {
      console.warn('Failed to hydrate auth state', error);
      window.localStorage.removeItem(STORAGE_KEY);
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await api.login(email, password);
    const identity: ClientIdentity = {
      clientId: response.client_id,
      name: response.name,
      primaryContact: response.primary_contact,
      role: 'client',
    };
    setUser(identity);
    setToken(response.token);
    api.setAuthContext(response.token, response.client_id);
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        token: response.token,
        clientId: response.client_id,
        name: response.name,
        primaryContact: response.primary_contact,
      }),
    );
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    api.setAuthContext(null, null);
    window.localStorage.removeItem(STORAGE_KEY);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(user && token),
      isLoading,
      login,
      logout,
    }),
    [user, token, isLoading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
