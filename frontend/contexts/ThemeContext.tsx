'use client';

import { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';
type EnterpriseTheme = 'default' | 'azure' | 'government' | 'high-contrast';

const ENTERPRISE_THEMES: EnterpriseTheme[] = ['default', 'azure', 'government', 'high-contrast'];
const ENTERPRISE_THEME_STORAGE_KEY = 'enterprise_theme';

function normalizeEnterpriseTheme(value: string | null | undefined): EnterpriseTheme {
  if (value && ENTERPRISE_THEMES.includes(value as EnterpriseTheme)) {
    return value as EnterpriseTheme;
  }
  return 'default';
}

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'light' | 'dark';
  enterpriseTheme: EnterpriseTheme;
  setEnterpriseTheme: (theme: EnterpriseTheme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Initialize from localStorage if available
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('theme') as Theme | null;
      return saved || 'dark';
    }
    return 'dark';
  });
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('dark');
  const [enterpriseTheme, setEnterpriseThemeState] = useState<EnterpriseTheme>(() => {
    if (typeof window !== 'undefined') {
      const localTheme = localStorage.getItem(ENTERPRISE_THEME_STORAGE_KEY);
      return normalizeEnterpriseTheme(localTheme);
    }
    return normalizeEnterpriseTheme(process.env.NEXT_PUBLIC_ENTERPRISE_THEME_PRESET);
  });

  useEffect(() => {
    const root = document.documentElement;
    
    const applyTheme = (isDark: boolean) => {
      if (isDark) {
        root.classList.add('dark');
        root.classList.remove('light');
        setResolvedTheme('dark');
      } else {
        root.classList.remove('dark');
        root.classList.add('light');
        setResolvedTheme('light');
      }
    };

    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      applyTheme(mediaQuery.matches);
      
      const handler = (e: MediaQueryListEvent) => applyTheme(e.matches);
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    } else {
      applyTheme(theme === 'dark');
    }
  }, [theme]);

  useEffect(() => {
    const root = document.documentElement;
    if (enterpriseTheme === 'default') {
      root.removeAttribute('data-enterprise-theme');
      return;
    }
    root.setAttribute('data-enterprise-theme', enterpriseTheme);
  }, [enterpriseTheme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem('theme', newTheme);
  };

  const setEnterpriseTheme = (newTheme: EnterpriseTheme) => {
    const normalizedTheme = normalizeEnterpriseTheme(newTheme);
    setEnterpriseThemeState(normalizedTheme);
    localStorage.setItem(ENTERPRISE_THEME_STORAGE_KEY, normalizedTheme);
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme, enterpriseTheme, setEnterpriseTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
