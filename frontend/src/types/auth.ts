import type { User as FirebaseUser } from 'firebase/auth';

/**
 * Application user interface.
 * This is a simplified version of Firebase's User object
 * containing only the fields we need in our app.
 */
export interface AuthUser {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
  emailVerified: boolean;
}

/**
 * Authentication state interface.
 * Represents the current state of authentication in the app.
 */
export interface AuthState {
  user: AuthUser | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
}

/**
 * Complete auth store interface including state and actions.
 * This defines all the properties and methods available in the Zustand store.
 */
export interface AuthStore extends AuthState {
  // State setters
  setUser: (user: FirebaseUser | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Authentication actions
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  refreshToken: () => Promise<string | null>;
}

/**
 * Firebase authentication error.
 * Used for type-safe error handling.
 */
export type AuthError = {
  code: string;
  message: string;
};
