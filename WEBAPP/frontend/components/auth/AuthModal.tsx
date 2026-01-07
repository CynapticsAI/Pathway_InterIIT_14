/**
 * Auth Modal Component - Modern Design
 * 
 * Updated with elevation, Lucide icons, and design system integration
 */

'use client';

import { useState } from 'react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Icon } from '../ui/Icon';
import { useAuth } from '@/hooks/useAuth';
import { showToast } from '@/utils/toast';
import { SUCCESS_MESSAGES } from '@/utils/constants';
import { getErrorMessage } from '@/lib/api';
import { cn } from '@/lib/utils';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  mode: 'login' | 'signup';
  onSwitchMode: () => void;
}

export function AuthModal({ isOpen, onClose, mode, onSwitchMode }: AuthModalProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);

  const { login, register } = useAuth();

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isSubmitting) return;

    // Validation for signup
    if (mode === 'signup') {
      if (!username.trim()) {
        showToast.error('Username is required');
        return;
      }
      if (password !== password2) {
        showToast.error('Passwords do not match');
        return;
      }
      if (password.length < 8) {
        showToast.error('Password must be at least 8 characters');
        return;
      }
    }

    setIsSubmitting(true);

    try {
      if (mode === 'login') {
        await login({ email, password });
        showToast.success(SUCCESS_MESSAGES.LOGIN);
        
        // Reset form and close
        setEmail('');
        setPassword('');
        onClose();
      } else {
        const [first_name, ...lastNameParts] = name.trim().split(' ');
        const last_name = lastNameParts.join(' ');

        const response = await register({ 
          username: username.trim(),
          email, 
          password,
          password2,
          first_name: first_name || undefined,
          last_name: last_name || undefined,
        });
        
        // Show the message from backend (email verification)
        showToast.success(response.message || SUCCESS_MESSAGES.REGISTER);
        
        // Reset form and close
        setEmail('');
        setPassword('');
        setPassword2('');
        setName('');
        setUsername('');
        onClose();
      }
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      showToast.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!email) {
      showToast.error('Please enter your email address first');
      return;
    }

    setIsSubmitting(true);
    try {
      const { authService } = await import('@/lib/api');
      await authService.forgotPassword({ email });
      showToast.success(SUCCESS_MESSAGES.PASSWORD_RESET_REQUEST);
      setShowForgotPassword(false);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      showToast.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className={cn(
        'relative w-full max-w-md mx-4 p-8',
        'bg-[var(--color-surface)]',
        'rounded-2xl elevation-6',
        'animate-fadeIn'
      )}>
        {/* Close Button */}
        <button
          onClick={onClose}
          className={cn(
            'absolute top-4 right-4',
            'text-[var(--color-muted)]',
            'hover:text-[var(--color-foreground)]',
            'transition-colors'
          )}
        >
          <Icon name="close" size="md" />
        </button>

        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-[var(--color-foreground)] mb-2">
            {mode === 'login' ? 'Welcome Back' : 'Create Account'}
          </h2>
          <p className="text-[var(--color-muted)] text-sm">
            {mode === 'login' 
              ? 'Login to access your stock portfolio' 
              : 'Sign up to start analyzing stocks'
            }
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'signup' && (
            <>
              <div>
                <label className="block text-sm font-medium text-[var(--color-foreground)] mb-1.5">
                  Username <span className="text-[var(--color-danger)]">*</span>
                </label>
                <Input
                  type="text"
                  placeholder="johndoe"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  fullWidth
                  required
                  variant="filled"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--color-foreground)] mb-1.5">
                  Full Name
                </label>
                <Input
                  type="text"
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  fullWidth
                  variant="filled"
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-sm font-medium text-[var(--color-foreground)] mb-1.5">
              Email
            </label>
            <Input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              fullWidth
              required
              variant="filled"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[var(--color-foreground)] mb-1.5">
              Password
            </label>
            <Input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              fullWidth
              required
              variant="filled"
            />
          </div>

          {mode === 'signup' && (
            <div>
              <label className="block text-sm font-medium text-[var(--color-foreground)] mb-1.5">
                Confirm Password <span className="text-[var(--color-danger)]">*</span>
              </label>
              <Input
                type="password"
                placeholder="••••••••"
                value={password2}
                onChange={(e) => setPassword2(e.target.value)}
                fullWidth
                required
                variant="filled"
              />
            </div>
          )}

          {mode === 'login' && (
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="rounded" />
                <span className="text-[var(--color-muted)]">Remember me</span>
              </label>
              <button 
                type="button" 
                onClick={() => setShowForgotPassword(true)}
                className="text-[var(--color-primary)] hover:underline"
                disabled={isSubmitting}
              >
                Forgot password?
              </button>
            </div>
          )}

          <Button 
            type="submit" 
            variant="primary" 
            className="w-full py-3 text-base"
            disabled={isSubmitting}
            isLoading={isSubmitting}
          >
            {isSubmitting 
              ? (mode === 'login' ? 'Logging in...' : 'Signing up...')
              : (mode === 'login' ? 'Login' : 'Sign Up')
            }
          </Button>
        </form>

        {/* Divider */}
        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-[var(--color-border)]" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-[var(--color-surface)] text-[var(--color-muted)]">
              Or continue with
            </span>
          </div>
        </div>

        {/* Social Login */}
        <div className="grid grid-cols-2 gap-3">
          <Button variant="secondary" className="w-full">
            <Icon name="globe" size="sm" className="mr-2" />
            Google
          </Button>
          <Button variant="secondary" className="w-full">
            GitHub
          </Button>
        </div>

        {/* Switch Mode */}
        <p className="mt-6 text-center text-sm text-[var(--color-muted)]">
          {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}{' '}
          <button
            type="button"
            onClick={onSwitchMode}
            className="text-[var(--color-primary)] font-medium hover:underline"
            disabled={isSubmitting}
          >
            {mode === 'login' ? 'Sign Up' : 'Login'}
          </button>
        </p>
      </div>

      {/* Forgot Password Modal */}
      {showForgotPassword && (
        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center rounded-2xl">
          <div className={cn(
            'max-w-sm w-full mx-4 p-6',
            'bg-[var(--color-surface)]',
            'rounded-xl elevation-6'
          )}>
            <h3 className="text-xl font-bold text-[var(--color-foreground)] mb-4">
              Reset Password
            </h3>
            <p className="text-sm text-[var(--color-muted)] mb-4">
              Enter your email address and we'll send you a link to reset your password.
            </p>
            <Input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              fullWidth
              className="mb-4"
              variant="filled"
            />
            <div className="flex gap-3">
              <Button
                variant="secondary"
                onClick={() => setShowForgotPassword(false)}
                className="flex-1"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleForgotPassword}
                className="flex-1"
                disabled={isSubmitting}
                isLoading={isSubmitting}
              >
                {isSubmitting ? 'Sending...' : 'Send Reset Link'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
