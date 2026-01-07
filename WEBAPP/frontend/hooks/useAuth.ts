// ============================================
// useAuth Hook
// Convenient hook for authentication
// ============================================

import { useAuthContext } from '@/contexts/AuthContext';

export const useAuth = () => {
  return useAuthContext();
};

export default useAuth;
