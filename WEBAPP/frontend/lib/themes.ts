/**
 * THEME CONFIGURATION SYSTEM
 * 
 * Easy theme switching - just change ACTIVE_THEME constant
 * All colors are automatically applied across the entire application
 */

export type ThemeName = 
  | 'sky-blue'      // Current theme - Professional Sky Blue
  | 'emerald-pro'   // Professional Green/Emerald
  | 'violet-luxury' // Luxury Purple/Violet
  | 'orange-energy' // Energetic Orange
  | 'rose-elegant'  // Elegant Rose/Pink
  | 'slate-minimal' // Minimal Gray/Slate
  | 'indigo-deep'   // Deep Indigo/Blue
  | 'teal-modern'   // Modern Teal/Cyan
  | 'amber-warm'    // Warm Amber/Yellow
  | 'red-bold';     // Bold Red/Crimson

export interface ThemeColors {
  name: string;
  description: string;
  colors: {
    // Primary brand color
    primary: string;
    primaryHover: string;
    
    // Success/Gain (always green for financial data)
    success: string;
    
    // Danger/Loss (always red for financial data)
    danger: string;
    
    // Accent color (used for highlights, badges, etc.)
    accent: string;
    accentHover: string;
    
    // Secondary action color
    secondary: string;
    secondaryHover: string;
    
    // Informational
    info: string;
    
    // Warning
    warning: string;
  };
}

// ============================================
// THEME PRESETS
// ============================================

export const THEME_PRESETS: Record<ThemeName, ThemeColors> = {
  // 1. Sky Blue - Current Professional Theme
  'sky-blue': {
    name: 'Sky Blue Professional',
    description: 'Clean, professional sky blue theme - Current default',
    colors: {
      primary: '#0EA5E9',        // Sky 500
      primaryHover: '#0284C7',   // Sky 600
      success: '#10B981',        // Emerald 500
      danger: '#EF4444',         // Red 500
      accent: '#06B6D4',         // Cyan 500
      accentHover: '#0891B2',    // Cyan 600
      secondary: '#3B82F6',      // Blue 500
      secondaryHover: '#2563EB', // Blue 600
      info: '#3B82F6',           // Blue 500
      warning: '#F59E0B',        // Amber 500
    },
  },

  // 2. Emerald Professional
  'emerald-pro': {
    name: 'Emerald Professional',
    description: 'Sophisticated green theme - Great for finance apps',
    colors: {
      primary: '#10B981',        // Emerald 500
      primaryHover: '#059669',   // Emerald 600
      success: '#10B981',        // Emerald 500
      danger: '#EF4444',         // Red 500
      accent: '#14B8A6',         // Teal 500
      accentHover: '#0D9488',    // Teal 600
      secondary: '#06B6D4',      // Cyan 500
      secondaryHover: '#0891B2', // Cyan 600
      info: '#06B6D4',           // Cyan 500
      warning: '#F59E0B',        // Amber 500
    },
  },

  // 3. Violet Luxury
  'violet-luxury': {
    name: 'Violet Luxury',
    description: 'Premium purple theme - Elegant and sophisticated',
    colors: {
      primary: '#8B5CF6',        // Violet 500
      primaryHover: '#7C3AED',   // Violet 600
      success: '#10B981',        // Emerald 500
      danger: '#EF4444',         // Red 500
      accent: '#A78BFA',         // Violet 400
      accentHover: '#8B5CF6',    // Violet 500
      secondary: '#EC4899',      // Pink 500
      secondaryHover: '#DB2777', // Pink 600
      info: '#6366F1',           // Indigo 500
      warning: '#F59E0B',        // Amber 500
    },
  },

  // 4. Orange Energy
  'orange-energy': {
    name: 'Orange Energy',
    description: 'Vibrant orange theme - Energetic and bold',
    colors: {
      primary: '#F97316',        // Orange 500
      primaryHover: '#EA580C',   // Orange 600
      success: '#10B981',        // Emerald 500
      danger: '#EF4444',         // Red 500
      accent: '#FB923C',         // Orange 400
      accentHover: '#F97316',    // Orange 500
      secondary: '#F59E0B',      // Amber 500
      secondaryHover: '#D97706', // Amber 600
      info: '#3B82F6',           // Blue 500
      warning: '#F59E0B',        // Amber 500
    },
  },

  // 5. Rose Elegant
  'rose-elegant': {
    name: 'Rose Elegant',
    description: 'Refined rose/pink theme - Elegant and modern',
    colors: {
      primary: '#F43F5E',        // Rose 500
      primaryHover: '#E11D48',   // Rose 600
      success: '#10B981',        // Emerald 500
      danger: '#EF4444',         // Red 500
      accent: '#FB7185',         // Rose 400
      accentHover: '#F43F5E',    // Rose 500
      secondary: '#EC4899',      // Pink 500
      secondaryHover: '#DB2777', // Pink 600
      info: '#3B82F6',           // Blue 500
      warning: '#F59E0B',        // Amber 500
    },
  },

  // 6. Slate Minimal
  'slate-minimal': {
    name: 'Slate Minimal',
    description: 'Minimalist gray theme - Clean and neutral',
    colors: {
      primary: '#475569',        // Slate 600
      primaryHover: '#334155',   // Slate 700
      success: '#10B981',        // Emerald 500
      danger: '#EF4444',         // Red 500
      accent: '#64748B',         // Slate 500
      accentHover: '#475569',    // Slate 600
      secondary: '#0EA5E9',      // Sky 500
      secondaryHover: '#0284C7', // Sky 600
      info: '#3B82F6',           // Blue 500
      warning: '#F59E0B',        // Amber 500
    },
  },

  // 7. Indigo Deep
  'indigo-deep': {
    name: 'Indigo Deep',
    description: 'Deep indigo theme - Professional and trustworthy',
    colors: {
      primary: '#6366F1',        // Indigo 500
      primaryHover: '#4F46E5',   // Indigo 600
      success: '#10B981',        // Emerald 500
      danger: '#EF4444',         // Red 500
      accent: '#818CF8',         // Indigo 400
      accentHover: '#6366F1',    // Indigo 500
      secondary: '#8B5CF6',      // Violet 500
      secondaryHover: '#7C3AED', // Violet 600
      info: '#3B82F6',           // Blue 500
      warning: '#F59E0B',        // Amber 500
    },
  },

  // 8. Teal Modern
  'teal-modern': {
    name: 'Teal Modern',
    description: 'Modern teal theme - Fresh and contemporary',
    colors: {
      primary: '#14B8A6',        // Teal 500
      primaryHover: '#0D9488',   // Teal 600
      success: '#10B981',        // Emerald 500
      danger: '#EF4444',         // Red 500
      accent: '#2DD4BF',         // Teal 400
      accentHover: '#14B8A6',    // Teal 500
      secondary: '#06B6D4',      // Cyan 500
      secondaryHover: '#0891B2', // Cyan 600
      info: '#06B6D4',           // Cyan 500
      warning: '#F59E0B',        // Amber 500
    },
  },

  // 9. Amber Warm
  'amber-warm': {
    name: 'Amber Warm',
    description: 'Warm amber theme - Friendly and inviting',
    colors: {
      primary: '#F59E0B',        // Amber 500
      primaryHover: '#D97706',   // Amber 600
      success: '#10B981',        // Emerald 500
      danger: '#EF4444',         // Red 500
      accent: '#FCD34D',         // Amber 300
      accentHover: '#F59E0B',    // Amber 500
      secondary: '#F97316',      // Orange 500
      secondaryHover: '#EA580C', // Orange 600
      info: '#3B82F6',           // Blue 500
      warning: '#F59E0B',        // Amber 500
    },
  },

  // 10. Red Bold
  'red-bold': {
    name: 'Red Bold',
    description: 'Bold red theme - Powerful and attention-grabbing',
    colors: {
      primary: '#DC2626',        // Red 600
      primaryHover: '#B91C1C',   // Red 700
      success: '#10B981',        // Emerald 500
      danger: '#EF4444',         // Red 500
      accent: '#EF4444',         // Red 500
      accentHover: '#DC2626',    // Red 600
      secondary: '#F97316',      // Orange 500
      secondaryHover: '#EA580C', // Orange 600
      info: '#3B82F6',           // Blue 500
      warning: '#F59E0B',        // Amber 500
    },
  },
};

// ============================================
// CHANGE THIS TO SWITCH THEMES!
// ============================================
export const ACTIVE_THEME: ThemeName = 'slate-minimal';

// Get current theme
export const getCurrentTheme = (): ThemeColors => {
  return THEME_PRESETS[ACTIVE_THEME];
};

// Get all available themes (for theme switcher UI)
export const getAllThemes = (): Array<{ key: ThemeName; config: ThemeColors }> => {
  return Object.entries(THEME_PRESETS).map(([key, config]) => ({
    key: key as ThemeName,
    config,
  }));
};

// Generate CSS variables for current theme
export const getThemeCSSVariables = (): Record<string, string> => {
  const theme = getCurrentTheme();
  return {
    '--color-primary': theme.colors.primary,
    '--color-primary-hover': theme.colors.primaryHover,
    '--color-success': theme.colors.success,
    '--color-danger': theme.colors.danger,
    '--color-accent': theme.colors.accent,
    '--color-accent-hover': theme.colors.accentHover,
    '--color-secondary': theme.colors.secondary,
    '--color-secondary-hover': theme.colors.secondaryHover,
    '--color-info': theme.colors.info,
    '--color-warning': theme.colors.warning,
  };
};

// Helper to apply theme to document
export const applyTheme = (themeName: ThemeName = ACTIVE_THEME) => {
  const theme = THEME_PRESETS[themeName];
  const root = document.documentElement;
  
  Object.entries(getThemeCSSVariables()).forEach(([property, value]) => {
    root.style.setProperty(property, value);
  });
  
  return theme;
};
