/**
 * Input & TextArea Components - Modern Design System
 * 
 * Professional input fields with elevation, consistent styling, and better focus states
 * Uses new design tokens and focus ring system
 */

import { InputHTMLAttributes, TextareaHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export type InputSize = 'sm' | 'md' | 'lg';
export type InputVariant = 'default' | 'filled' | 'flushed';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  fullWidth?: boolean;
  inputSize?: InputSize;
  variant?: InputVariant;
  error?: boolean;
  helperText?: string;
}

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  fullWidth?: boolean;
  inputSize?: InputSize;
  variant?: InputVariant;
  error?: boolean;
  helperText?: string;
}

const inputBaseStyles = cn(
  'rounded-lg',
  'bg-[var(--color-surface)] text-[var(--color-text-primary)]',
  'placeholder:text-[var(--color-text-tertiary)]',
  'transition-smooth focus-ring',
  'disabled:opacity-50 disabled:cursor-not-allowed'
);

const inputSizes: Record<InputSize, string> = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-4 text-base',
};

const inputVariants: Record<InputVariant, string> = {
  default: cn(
    'border border-[var(--color-border)]',
    'hover:border-[var(--color-border-hover)]',
    'focus:border-[var(--color-border-focus)]',
    'elevation-1'
  ),
  filled: cn(
    'bg-[var(--color-surface-elevated)]',
    'border-2 border-transparent',
    'hover:bg-[var(--color-surface-hover)]',
    'focus:border-[var(--color-primary)]'
  ),
  flushed: cn(
    'rounded-none border-0 border-b-2',
    'border-[var(--color-border)]',
    'hover:border-[var(--color-border-hover)]',
    'focus:border-[var(--color-primary)]',
    'px-0'
  ),
};

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ 
    fullWidth = false, 
    inputSize = 'md',
    variant = 'default',
    error = false,
    helperText,
    className = '', 
    ...props 
  }, ref) => {
    return (
      <div className={cn('flex flex-col gap-1', fullWidth && 'w-full')}>
        <input
          ref={ref}
          className={cn(
            inputBaseStyles,
            inputSizes[inputSize],
            inputVariants[variant],
            error && 'border-[var(--color-loss)] focus:border-[var(--color-loss)]',
            fullWidth && 'w-full',
            className
          )}
          {...props}
        />
        {helperText && (
          <span className={cn(
            'text-xs',
            error ? 'text-[var(--color-loss)]' : 'text-[var(--color-text-tertiary)]'
          )}>
            {helperText}
          </span>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ 
    fullWidth = false,
    inputSize = 'md',
    variant = 'default',
    error = false,
    helperText,
    className = '', 
    ...props 
  }, ref) => {
    return (
      <div className={cn('flex flex-col gap-1', fullWidth && 'w-full')}>
        <textarea
          ref={ref}
          className={cn(
            inputBaseStyles,
            'py-3 min-h-[100px]',
            inputVariants[variant],
            error && 'border-[var(--color-loss)] focus:border-[var(--color-loss)]',
            fullWidth && 'w-full',
            'resize-none',
            className
          )}
          {...props}
        />
        {helperText && (
          <span className={cn(
            'text-xs',
            error ? 'text-[var(--color-loss)]' : 'text-[var(--color-text-tertiary)]'
          )}>
            {helperText}
          </span>
        )}
      </div>
    );
  }
);

TextArea.displayName = 'TextArea';
