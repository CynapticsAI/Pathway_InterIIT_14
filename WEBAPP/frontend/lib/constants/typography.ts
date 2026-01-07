/**
 * Typography System
 * 
 * Consistent type scale and font definitions for the application
 */

export const typography = {
  // Font Families
  fonts: {
    sans: 'var(--font-open-sans), "Open Sans", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Courier New", monospace',
  },

  // Font Sizes with line heights
  sizes: {
    xs: {
      fontSize: '0.75rem',    // 12px
      lineHeight: '1rem',     // 16px
    },
    sm: {
      fontSize: '0.875rem',   // 14px
      lineHeight: '1.25rem',  // 20px
    },
    base: {
      fontSize: '1rem',       // 16px
      lineHeight: '1.5rem',   // 24px
    },
    lg: {
      fontSize: '1.125rem',   // 18px
      lineHeight: '1.75rem',  // 28px
    },
    xl: {
      fontSize: '1.25rem',    // 20px
      lineHeight: '1.75rem',  // 28px
    },
    '2xl': {
      fontSize: '1.5rem',     // 24px
      lineHeight: '2rem',     // 32px
    },
    '3xl': {
      fontSize: '1.875rem',   // 30px
      lineHeight: '2.25rem',  // 36px
    },
    '4xl': {
      fontSize: '2.25rem',    // 36px
      lineHeight: '2.5rem',   // 40px
    },
  },

  // Font Weights
  weights: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  // Letter Spacing
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },

  // Semantic Typography Tokens
  semantic: {
    display: {
      fontSize: '2rem',       // 32px
      lineHeight: '2.5rem',   // 40px
      fontWeight: 700,
      letterSpacing: '-0.025em',
    },
    h1: {
      fontSize: '1.5rem',     // 24px
      lineHeight: '2rem',     // 32px
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    h2: {
      fontSize: '1.25rem',    // 20px
      lineHeight: '1.75rem',  // 28px
      fontWeight: 600,
      letterSpacing: '0',
    },
    h3: {
      fontSize: '1.125rem',   // 18px
      lineHeight: '1.5rem',   // 24px
      fontWeight: 600,
      letterSpacing: '0',
    },
    body: {
      fontSize: '1rem',       // 16px
      lineHeight: '1.5rem',   // 24px
      fontWeight: 400,
      letterSpacing: '0',
    },
    bodySmall: {
      fontSize: '0.875rem',   // 14px
      lineHeight: '1.25rem',  // 20px
      fontWeight: 400,
      letterSpacing: '0',
    },
    caption: {
      fontSize: '0.75rem',    // 12px
      lineHeight: '1rem',     // 16px
      fontWeight: 400,
      letterSpacing: '0.025em',
    },
    button: {
      fontSize: '0.875rem',   // 14px
      lineHeight: '1.25rem',  // 20px
      fontWeight: 500,
      letterSpacing: '0.025em',
    },
    code: {
      fontSize: '0.875rem',   // 14px
      lineHeight: '1.25rem',  // 20px
      fontWeight: 400,
      fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Courier New", monospace',
    },
  },
} as const;

export type TypographySize = keyof typeof typography.sizes;
export type TypographyWeight = keyof typeof typography.weights;
export type SemanticTypography = keyof typeof typography.semantic;
