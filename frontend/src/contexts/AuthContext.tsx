import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { jwtDecode } from 'jwt-decode';

import { toast } from 'sonner';

import { loginRequest, setAuthToken, type AuthResponse, type UserProfile } from '@/services/api';

export type UserRole = 'admin' | 'manager' | 'sales' | 'tech' | 'service';

interface DecodedToken {
  sub: string;
  exp?: number;
  email?: string;
  name?: string;
  role?: UserRole;
}

interface AuthContextValue {
  user: UserProfile | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_STORAGE_KEY = 'ai-seo-dashboard.token';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const persisted = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!persisted) {
      setLoading(false);
      return;
    }
    try {
      setAuthToken(persisted);
      const decoded = jwtDecode<DecodedToken>(persisted);
      if (decoded.exp && decoded.exp * 1000 < Date.now()) {
        window.localStorage.removeItem(TOKEN_STORAGE_KEY);
        setAuthToken(null);
        setLoading(false);
        return;
      }
      const profile: UserProfile = {
        id: decoded.sub,
        email: decoded.email ?? '',
        name: decoded.name ?? 'User',
        role: decoded.role ?? 'sales'
      };
      setUser(profile);
      setTokenState(persisted);
    } catch (error) {
      console.error('Failed to restore session', error);
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
      setAuthToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const persistSession = useCallback((auth: AuthResponse) => {
    const decoded = jwtDecode<DecodedToken>(auth.accessToken);
    const profile: UserProfile = {
      id: decoded.sub,
      email: decoded.email ?? auth.user.email,
      name: decoded.name ?? auth.user.name,
      role: decoded.role ?? auth.user.role
    };
    setUser(profile);
    setTokenState(auth.accessToken);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, auth.accessToken);
    setAuthToken(auth.accessToken);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      setLoading(true);
      try {
        const response = await loginRequest({ email, password });
        persistSession(response);
      } catch (error) {
        console.error('Login failed', error);
        toast.error('Unable to sign in. Please check your credentials.');
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [persistSession]
  );

  const logout = useCallback(() => {
    setUser(null);
    setTokenState(null);
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setAuthToken(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      login,
      logout
    }),
    [loading, login, logout, token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
