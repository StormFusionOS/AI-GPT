import React, { createContext, useContext, useMemo, useState } from 'react';

export type Role = 'SALES' | 'SALES_MANAGER' | 'OWNER';

type AuthState = {
  token: string | null;
  role: Role | null;
  login: (token: string, role: Role) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthState | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [role, setRole] = useState<Role | null>(null);

  const value = useMemo(
    () => ({
      token,
      role,
      login: (newToken: string, newRole: Role) => {
        setToken(newToken);
        setRole(newRole);
      },
      logout: () => {
        setToken(null);
        setRole(null);
      },
    }),
    [token, role]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('Auth context missing');
  }
  return ctx;
};
