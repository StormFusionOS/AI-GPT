import { createContext, useContext, useEffect, useMemo, useState } from 'react';

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: 'light' | 'dark';
  storageKey?: string;
}

interface ThemeContextValue {
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeProvider({
  children,
  defaultTheme = 'light',
  storageKey = 'theme',
}: ThemeProviderProps) {
  const [theme, setThemeState] = useState<'light' | 'dark'>(() => {
    if (typeof window === 'undefined') {
      return defaultTheme;
    }
    const stored = window.localStorage.getItem(storageKey) as 'light' | 'dark' | null;
    return stored ?? defaultTheme;
  });

  useEffect(() => {
    document.documentElement.classList.remove(theme === 'light' ? 'dark' : 'light');
    document.documentElement.classList.add(theme);
    window.localStorage.setItem(storageKey, theme);
  }, [theme, storageKey]);

  const value = useMemo<ThemeContextValue>(() => ({ theme, setTheme: setThemeState }), [theme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return ctx;
}
