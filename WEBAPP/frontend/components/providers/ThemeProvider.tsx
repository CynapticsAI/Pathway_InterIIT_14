/**
 * Theme Provider Component
 * 
 * Applies the active theme colors to the application
 */

'use client';

import { useEffect } from 'react';
import { getCurrentTheme } from '@/lib/themes';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Apply theme on mount and whenever it changes
    const theme = getCurrentTheme();
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
    
    console.log('🎨 Theme applied:', theme.name);
  }, []);

  return <>{children}</>;
}
