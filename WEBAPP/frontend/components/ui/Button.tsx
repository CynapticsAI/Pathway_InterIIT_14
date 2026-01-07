/**
 * Button Component - Modern Design System
 * 
 * Professional button with elevation, consistent sizing, and semantic variants
 * Uses new design tokens and elevation system (no gradients!)
 */

import { ButtonHTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/utils';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger' | 'success';
export type ButtonSize = 'sm' | 'md' | 'lg' | 'icon';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: ReactNode;
  fullWidth?: boolean;
  isLoading?: boolean;
}

export function Button({ 
  variant = 'primary', 
  size = 'md', 
  children, 
  className = '',
  fullWidth = false,
  isLoading = false,
  disabled,
  ...props 
}: ButtonProps) {
  const baseStyles = cn(
    'inline-flex items-center justify-center gap-2',
    'font-medium rounded-lg',
    'transition-smooth focus-ring',
    'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
    fullWidth && 'w-full'
  );
  
  const variants: Record<ButtonVariant, string> = {
    primary: cn(
      'bg-[var(--color-primary)] text-white',
      'elevation-2 hover-elevate',
      'hover:bg-[var(--color-primary-hover)]',
      'active:scale-95'
    ),
    secondary: cn(
      'bg-[var(--color-surface-elevated)] text-[var(--color-text-primary)]',
      'elevation-1 hover-elevate',
      'hover:bg-[var(--color-surface-hover)]'
    ),
    outline: cn(
      'bg-transparent text-[var(--color-text-primary)]',
      'border border-[var(--color-border)]',
      'hover:bg-[var(--color-surface-elevated)]',
      'hover:border-[var(--color-border-hover)]'
    ),
    ghost: cn(
      'bg-transparent text-[var(--color-text-secondary)]',
      'hover:bg-[var(--color-surface-elevated)]',
      'hover:text-[var(--color-text-primary)]'
    ),
    danger: cn(
      'bg-[var(--color-loss)] text-white',
      'elevation-2 hover-elevate',
      'hover:opacity-90',
      'active:scale-95'
    ),
    success: cn(
      'bg-[var(--color-gain)] text-white',
      'elevation-2 hover-elevate',
      'hover:opacity-90',
      'active:scale-95'
    ),
  };
  
  const sizes: Record<ButtonSize, string> = {
    sm: 'h-8 px-3 text-sm',
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-6 text-base',
    icon: 'h-10 w-10 p-0',
  };

  return (
    <button 
      className={cn(
        baseStyles,
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <span>Loading...</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}
