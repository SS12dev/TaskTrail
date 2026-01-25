import { useAuthStore } from '../stores/authStore';

/**
 * Custom hook to access auth state and actions.
 *
 * This hook provides a clean, type-safe API for components to interact
 * with the authentication system. It's a wrapper around the Zustand store
 * that makes it easy to use auth in any component.
 *
 * Example usage:
 *   const { user, isAuthenticated, login, logout } = useAuth();
 *
 *   if (isAuthenticated) {
 *     return <div>Welcome {user?.email}</div>;
 *   }
 *
 * @returns Auth state and action methods
 */
export const useAuth = () => {
  const {
    user,
    loading,
    error,
    isAuthenticated,
    login,
    loginWithGoogle,
    register,
    logout,
    resetPassword,
    refreshToken,
    setError,
  } = useAuthStore();

  return {
    // Current auth state
    user,
    loading,
    error,
    isAuthenticated,

    // Authentication actions
    login,
    loginWithGoogle,
    register,
    logout,
    resetPassword,
    refreshToken,

    // Utility methods
    clearError: () => setError(null),
  };
};
