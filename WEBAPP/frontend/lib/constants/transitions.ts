/**
 * Transition & Animation System
 * 
 * Consistent timing functions and durations for animations
 */

export const transitions = {
  // Durations (in milliseconds)
  duration: {
    instant: 0,
    fast: 150,
    normal: 200,
    slow: 300,
    slower: 500,
  },

  // Timing Functions (Easing)
  easing: {
    linear: 'linear',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    // Custom easings for smooth interactions
    smooth: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  },

  // Common transition strings
  default: 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)',
  fast: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)',
  slow: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
  
  // Specific property transitions
  color: 'color 200ms cubic-bezier(0.4, 0, 0.2, 1)',
  background: 'background-color 200ms cubic-bezier(0.4, 0, 0.2, 1)',
  transform: 'transform 200ms cubic-bezier(0.4, 0, 0.2, 1)',
  opacity: 'opacity 200ms cubic-bezier(0.4, 0, 0.2, 1)',
  shadow: 'box-shadow 200ms cubic-bezier(0.4, 0, 0.2, 1)',
} as const;

/**
 * Common animations as CSS keyframes
 */
export const animations = {
  fadeIn: {
    name: 'fadeIn',
    keyframes: `
      from { opacity: 0; }
      to { opacity: 1; }
    `,
    duration: transitions.duration.normal,
  },
  
  fadeOut: {
    name: 'fadeOut',
    keyframes: `
      from { opacity: 1; }
      to { opacity: 0; }
    `,
    duration: transitions.duration.normal,
  },
  
  slideUp: {
    name: 'slideUp',
    keyframes: `
      from { transform: translateY(10px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    `,
    duration: transitions.duration.normal,
  },
  
  slideDown: {
    name: 'slideDown',
    keyframes: `
      from { transform: translateY(-10px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    `,
    duration: transitions.duration.normal,
  },
  
  scaleIn: {
    name: 'scaleIn',
    keyframes: `
      from { transform: scale(0.95); opacity: 0; }
      to { transform: scale(1); opacity: 1; }
    `,
    duration: transitions.duration.normal,
  },

  pulse: {
    name: 'pulse',
    keyframes: `
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    `,
    duration: 2000,
  },

  spin: {
    name: 'spin',
    keyframes: `
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    `,
    duration: 1000,
  },
} as const;

export type TransitionDuration = keyof typeof transitions.duration;
export type TransitionEasing = keyof typeof transitions.easing;
export type AnimationName = keyof typeof animations;
