/**
 * Theme Provider - Manages light/dark mode AND color themes
 * 
 * Now applies both dark/light mode AND the active color theme with dynamic switching
 */

'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getCurrentTheme, THEME_PRESETS, type ThemeName } from '@/lib/themes';

interface ThemeContextType {
  isDark: boolean;
  toggleTheme: () => void;
  theme: 'light' | 'dark';
  colorTheme: ThemeName;
  setColorTheme: (theme: ThemeName) => void;
  availableThemes: typeof THEME_PRESETS;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [colorTheme, setColorThemeState] = useState<ThemeName>('sky-blue');

  // Apply color theme
  const applyColorTheme = (themeName: ThemeName) => {
    const theme = THEME_PRESETS[themeName];
    const root = document.documentElement;
    
    // Apply theme colors as CSS variables
    root.style.setProperty('--color-primary', theme.colors.primary);
    root.style.setProperty('--color-primary-hover', theme.colors.primaryHover);
    root.style.setProperty('--color-success', theme.colors.success);
    root.style.setProperty('--color-danger', theme.colors.danger);
    root.style.setProperty('--color-accent', theme.colors.accent);
    root.style.setProperty('--color-accent-hover', theme.colors.accentHover);
    root.style.setProperty('--color-secondary', theme.colors.secondary);
    root.style.setProperty('--color-secondary-hover', theme.colors.secondaryHover);
    root.style.setProperty('--color-info', theme.colors.info);
    root.style.setProperty('--color-warning', theme.colors.warning);
    
    // Also update border focus color to match primary
    root.style.setProperty('--color-border-focus', theme.colors.primary);
    
    console.log('🎨 Color Theme Applied:', theme.name, theme.colors.primary);
  };

  // Set color theme and save to localStorage
  const setColorTheme = (themeName: ThemeName) => {
    setColorThemeState(themeName);
    localStorage.setItem('colorTheme', themeName);
    applyColorTheme(themeName);
  };

  // Load color theme from localStorage or use default
  useEffect(() => {
    const savedColorTheme = localStorage.getItem('colorTheme') as ThemeName;
    if (savedColorTheme && THEME_PRESETS[savedColorTheme]) {
      setColorThemeState(savedColorTheme);
      applyColorTheme(savedColorTheme);
    } else {
      // Use default theme from themes.ts
      const defaultTheme = getCurrentTheme();
      const themeName = Object.entries(THEME_PRESETS).find(
        ([_, config]) => config.colors.primary === defaultTheme.colors.primary
      )?.[0] as ThemeName || 'sky-blue';
      setColorThemeState(themeName);
      applyColorTheme(themeName);
    }
  }, []);

  // Load light/dark mode from localStorage on mount
  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme) {
      const isDarkMode = savedTheme === 'dark';
      setIsDark(isDarkMode);
      updateThemeClass(isDarkMode);
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setIsDark(prefersDark);
      updateThemeClass(prefersDark);
    }
  }, []);

  const updateThemeClass = (dark: boolean) => {
    if (dark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
    updateThemeClass(newTheme);
  };

  return (
    <ThemeContext.Provider value={{ 
      isDark, 
      toggleTheme,
      theme: isDark ? 'dark' : 'light',
      colorTheme,
      setColorTheme,
      availableThemes: THEME_PRESETS,
    }}>
      {/* Prevent flash of wrong theme during initial mount */}
      <div style={{ visibility: mounted ? 'visible' : 'hidden' }}>
        {children}
      </div>
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    // During SSR or build time, return a default context instead of throwing
    if (typeof window === 'undefined') {
      return {
        isDark: false,
        toggleTheme: () => {},
        theme: 'light' as const,
        colorTheme: 'sky-blue' as ThemeName,
        setColorTheme: () => {},
        availableThemes: THEME_PRESETS,
      };
    }
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
