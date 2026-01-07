/**
 * Color Palette - Professional Financial Theme
 * 
 * A cohesive color system designed for financial applications
 * with emphasis on trust, clarity, and data visualization.
 */

export const colors = {
  // Primary Colors - Trust & Stability
  slate: {
    50: '#F8FAFC',
    100: '#F1F5F9',
    200: '#E2E8F0',
    300: '#CBD5E1',
    400: '#94A3B8',
    500: '#64748B',
    600: '#475569',
    700: '#334155',
    800: '#1E293B',
    900: '#0F172A',
  },

  // Accent Colors - Action & Data
  blue: {
    50: '#EFF6FF',
    100: '#DBEAFE',
    200: '#BFDBFE',
    300: '#93C5FD',
    400: '#60A5FA',
    500: '#3B82F6',
    600: '#2563EB',
    700: '#1D4ED8',
    800: '#1E40AF',
    900: '#1E3A8A',
  },

  sky: {
    400: '#38BDF8',
    500: '#0EA5E9',
    600: '#0284C7',
  },

  // Financial Data Colors
  success: {
    50: '#F0FDF4',
    100: '#DCFCE7',
    500: '#10B981',
    600: '#059669',
    700: '#047857',
  },

  warning: {
    50: '#FFFBEB',
    100: '#FEF3C7',
    500: '#F59E0B',
    600: '#D97706',
    700: '#B45309',
  },

  danger: {
    50: '#FEF2F2',
    100: '#FEE2E2',
    500: '#EF4444',
    600: '#DC2626',
    700: '#B91C1C',
  },

  // Neutral Colors
  neutral: {
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
  },

  // Special Colors
  white: '#FFFFFF',
  black: '#000000',
} as const;

/**
 * Semantic Color Tokens
 * Maps color values to their semantic meanings
 */
export const semanticColors = {
  light: {
    // Surface Colors
    background: colors.slate[50],
    surface: colors.white,
    surfaceElevated: colors.slate[100],
    surfaceHover: colors.slate[200],

    // Text Colors
    textPrimary: colors.slate[900],
    textSecondary: colors.slate[600],
    textTertiary: colors.slate[500],
    textInverse: colors.white,

    // Border Colors
    border: colors.slate[200],
    borderHover: colors.slate[300],
    borderFocus: colors.sky[500],

    // Action Colors
    primary: colors.sky[500],
    primaryHover: colors.sky[600],
    secondary: colors.blue[500],
    secondaryHover: colors.blue[600],

    // Financial Colors
    gain: colors.success[500],
    loss: colors.danger[500],
    warning: colors.warning[500],
    info: colors.blue[500],
    neutral: colors.neutral[500],
  },

  dark: {
    // Surface Colors
    background: colors.slate[900],
    surface: colors.slate[800],
    surfaceElevated: colors.slate[700],
    surfaceHover: colors.slate[600],

    // Text Colors
    textPrimary: colors.slate[50],
    textSecondary: colors.slate[300],
    textTertiary: colors.slate[400],
    textInverse: colors.slate[900],

    // Border Colors
    border: colors.slate[700],
    borderHover: colors.slate[600],
    borderFocus: colors.sky[400],

    // Action Colors
    primary: colors.sky[400],
    primaryHover: colors.sky[500],
    secondary: colors.blue[400],
    secondaryHover: colors.blue[500],

    // Financial Colors
    gain: colors.success[500],
    loss: colors.danger[500],
    warning: colors.warning[500],
    info: colors.blue[400],
    neutral: colors.neutral[500],
  },
} as const;

export type ColorMode = 'light' | 'dark';
export type SemanticColorKey = keyof typeof semanticColors.light;
