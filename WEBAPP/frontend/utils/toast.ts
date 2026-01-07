// ============================================
// Toast Notification Utilities
// Wrapper around react-hot-toast
// ============================================

import toast, { Toaster } from 'react-hot-toast';

// Toast configuration
const toastConfig = {
  duration: 4000,
  position: 'top-right' as const,
  style: {
    background: 'var(--color-background)',
    color: 'var(--color-foreground)',
    border: '1px solid var(--color-border)',
    borderRadius: '12px',
    padding: '16px',
    fontSize: '14px',
  },
  success: {
    iconTheme: {
      primary: '#10b981',
      secondary: '#fff',
    },
  },
  error: {
    iconTheme: {
      primary: '#ef4444',
      secondary: '#fff',
    },
  },
};

// ============================================
// TOAST METHODS
// ============================================

export const showToast = {
  success: (message: string) => {
    toast.success(message, toastConfig);
  },

  error: (message: string) => {
    toast.error(message, toastConfig);
  },

  loading: (message: string) => {
    return toast.loading(message, toastConfig);
  },

  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string;
      error: string;
    }
  ) => {
    return toast.promise(
      promise,
      {
        loading: messages.loading,
        success: messages.success,
        error: messages.error,
      },
      toastConfig
    );
  },

  dismiss: (toastId?: string) => {
    if (toastId) {
      toast.dismiss(toastId);
    } else {
      toast.dismiss();
    }
  },

  custom: (message: string) => {
    toast(message, toastConfig);
  },
};

// Export Toaster component for App layout
export { Toaster };

export default showToast;
