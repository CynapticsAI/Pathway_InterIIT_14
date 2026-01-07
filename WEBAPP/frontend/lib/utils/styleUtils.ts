/**
 * Style Utilities
 * 
 * Helper functions for working with design tokens
 */

import { semanticColors, type ColorMode } from '../constants/colors';
import { semanticShadows, darkSemanticShadows } from '../constants/shadows';

/**
 * Get semantic color value based on current theme
 */
export function getSemanticColor(
  key: keyof typeof semanticColors.light,
  mode: ColorMode = 'light'
): string {
  return semanticColors[mode][key];
}

/**
 * Get semantic shadow value based on current theme
 */
export function getSemanticShadow(
  key: keyof typeof semanticShadows,
  isDark: boolean = false
): string {
  return isDark ? darkSemanticShadows[key] : semanticShadows[key];
}

/**
 * Convert hex color to RGB values
 */
export function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

/**
 * Add alpha transparency to hex color
 */
export function hexWithAlpha(hex: string, alpha: number): string {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
}

/**
 * Format number as currency
 */
export function formatCurrency(value: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format number as percentage
 */
export function formatPercentage(value: number, decimals: number = 2): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
}

/**
 * Get color based on numeric value (for gain/loss)
 */
export function getValueColor(value: number, mode: ColorMode = 'light'): string {
  if (value > 0) return semanticColors[mode].gain;
  if (value < 0) return semanticColors[mode].loss;
  return semanticColors[mode].neutral;
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}
