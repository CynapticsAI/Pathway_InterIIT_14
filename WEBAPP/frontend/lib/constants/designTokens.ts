/**
 * Design Tokens - Main Export
 * 
 * Central location for all design system values.
 * Import this file to access colors, typography, spacing, shadows, etc.
 */

export { colors, semanticColors } from './colors';
export type { ColorMode, SemanticColorKey } from './colors';

export { typography } from './typography';
export type { TypographySize, TypographyWeight, SemanticTypography } from './typography';

export { spacing, semanticSpacing } from './spacing';
export type { SpacingKey, SemanticSpacingKey } from './spacing';

export { shadows, darkShadows, semanticShadows, darkSemanticShadows } from './shadows';
export type { ShadowSize, SemanticShadow } from './shadows';

export { borderRadius, semanticBorderRadius } from './borderRadius';
export type { BorderRadiusSize } from './borderRadius';

export { transitions, animations } from './transitions';
export type { TransitionDuration, TransitionEasing, AnimationName } from './transitions';

/**
 * Breakpoints for responsive design
 */
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;

/**
 * Z-Index Scale
 * Consistent layering system
 */
export const zIndex = {
  base: 0,
  dropdown: 1000,
  sticky: 1100,
  fixed: 1200,
  modalBackdrop: 1300,
  modal: 1400,
  popover: 1500,
  tooltip: 1600,
  toast: 1700,
} as const;

/**
 * Component Sizes
 * Standard size variants for components
 */
export const componentSizes = {
  button: {
    sm: { height: '32px', padding: '0 12px', fontSize: '14px' },
    md: { height: '40px', padding: '0 16px', fontSize: '14px' },
    lg: { height: '48px', padding: '0 24px', fontSize: '16px' },
    xl: { height: '56px', padding: '0 32px', fontSize: '18px' },
  },
  input: {
    sm: { height: '32px', padding: '0 12px', fontSize: '14px' },
    md: { height: '40px', padding: '0 14px', fontSize: '14px' },
    lg: { height: '48px', padding: '0 16px', fontSize: '16px' },
  },
  icon: {
    xs: '16px',
    sm: '20px',
    md: '24px',
    lg: '32px',
    xl: '40px',
  },
} as const;

/**
 * Opacity Scale
 */
export const opacity = {
  0: '0',
  5: '0.05',
  10: '0.1',
  20: '0.2',
  30: '0.3',
  40: '0.4',
  50: '0.5',
  60: '0.6',
  70: '0.7',
  80: '0.8',
  90: '0.9',
  95: '0.95',
  100: '1',
} as const;

export type Breakpoint = keyof typeof breakpoints;
export type ZIndexLayer = keyof typeof zIndex;
