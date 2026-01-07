/**
 * Elevation System (Shadows)
 * 
 * Professional elevation system using subtle shadows
 * Replaces borders for a modern, elevated look
 */

export const shadows = {
  // No shadow
  none: 'none',

  // Elevation Levels
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  
  base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
  
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
  
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
  
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
  
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',

  // Inner shadow
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)',
} as const;

/**
 * Dark Mode Shadows
 * Lighter shadows for dark backgrounds
 */
export const darkShadows = {
  none: 'none',
  
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
  
  base: '0 1px 3px 0 rgba(0, 0, 0, 0.4), 0 1px 2px -1px rgba(0, 0, 0, 0.4)',
  
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -2px rgba(0, 0, 0, 0.4)',
  
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -4px rgba(0, 0, 0, 0.5)',
  
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.6)',
  
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.7)',

  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.3)',
} as const;

/**
 * Semantic Shadow Tokens
 * Component-specific shadow definitions
 */
export const semanticShadows = {
  // Component Shadows
  card: shadows.md,
  cardHover: shadows.lg,
  
  button: shadows.sm,
  buttonHover: shadows.base,
  
  dropdown: shadows.lg,
  modal: shadows.xl,
  popover: shadows.md,
  
  // Special Effects
  focus: '0 0 0 3px rgba(14, 165, 233, 0.3)', // Sky blue focus ring
  error: '0 0 0 3px rgba(239, 68, 68, 0.3)',  // Red error ring
  success: '0 0 0 3px rgba(16, 185, 129, 0.3)', // Green success ring
} as const;

/**
 * Dark Mode Semantic Shadows
 */
export const darkSemanticShadows = {
  card: darkShadows.md,
  cardHover: darkShadows.lg,
  
  button: darkShadows.sm,
  buttonHover: darkShadows.base,
  
  dropdown: darkShadows.lg,
  modal: darkShadows.xl,
  popover: darkShadows.md,
  
  focus: '0 0 0 3px rgba(14, 165, 233, 0.5)',
  error: '0 0 0 3px rgba(239, 68, 68, 0.5)',
  success: '0 0 0 3px rgba(16, 185, 129, 0.5)',
} as const;

export type ShadowSize = keyof typeof shadows;
export type SemanticShadow = keyof typeof semanticShadows;
