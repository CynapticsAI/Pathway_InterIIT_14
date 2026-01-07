/**
 * Border Radius System
 * 
 * Consistent border radius values for rounded corners
 */

export const borderRadius = {
  none: '0',
  sm: '0.25rem',    // 4px
  base: '0.375rem', // 6px
  md: '0.5rem',     // 8px
  lg: '0.75rem',    // 12px
  xl: '1rem',       // 16px
  '2xl': '1.5rem',  // 24px
  '3xl': '2rem',    // 32px
  full: '9999px',   // Fully rounded
} as const;

/**
 * Semantic Border Radius
 */
export const semanticBorderRadius = {
  button: borderRadius.md,
  card: borderRadius.lg,
  input: borderRadius.md,
  badge: borderRadius.full,
  modal: borderRadius.xl,
  avatar: borderRadius.full,
  chip: borderRadius.full,
} as const;

export type BorderRadiusSize = keyof typeof borderRadius;
