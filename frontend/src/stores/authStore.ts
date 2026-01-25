import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  sendPasswordResetEmail,
  updateProfile,
  onAuthStateChanged,
} from 'firebase/auth';
import type { User as FirebaseUser } from 'firebase/auth';
import { auth } from '../config/firebase';
import type { AuthStore, AuthUser } from '../types/auth';

/**
 * Convert Firebase User object to our simplified AuthUser interface.
 * This extracts only the fields we need for the application.
 */
const mapFirebaseUser = (user: FirebaseUser | null): AuthUser | null => {
  if (!user) return null;

  return {
    uid: user.uid,
    email: user.email,
    displayName: user.displayName,
    photoURL: user.photoURL,
    emailVerified: user.emailVerified,
  };
};

// Configure Google OAuth provider
// prompt: 'select_account' forces account selection even if user is already signed in
const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({
  prompt: 'select_account',
});

/**
 * Zustand auth store with persistence.
 *
 * This store manages all authentication state and operations.
 * It uses Zustand for state management and persists user data to localStorage
 * so authentication survives page refreshes.
 *
 * Usage in components:
 *   const { user, login, logout } = useAuthStore();
 */
export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      loading: true, // Start with loading true while checking auth state
      error: null,
      isAuthenticated: false,

      // Set user from Firebase auth listener
      setUser: (user: FirebaseUser | null) => {
        const authUser = mapFirebaseUser(user);
        set({
          user: authUser,
          isAuthenticated: !!authUser,
          loading: false,
          error: null,
        });
      },

      // Set loading state
      setLoading: (loading: boolean) => set({ loading }),

      // Set error message
      setError: (error: string | null) => set({ error }),

      // Login with email and password
      login: async (email: string, password: string) => {
        try {
          set({ loading: true, error: null });
          const userCredential = await signInWithEmailAndPassword(auth, email, password);
          set({ user: mapFirebaseUser(userCredential.user), isAuthenticated: true });
        } catch (error: any) {
          const errorMessage = getAuthErrorMessage(error.code);
          set({ error: errorMessage });
          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Login with Google OAuth
      loginWithGoogle: async () => {
        try {
          set({ loading: true, error: null });
          const userCredential = await signInWithPopup(auth, googleProvider);
          set({ user: mapFirebaseUser(userCredential.user), isAuthenticated: true });
        } catch (error: any) {
          // Don't set error if user just closed the popup
          if (error.code !== 'auth/popup-closed-by-user') {
            const errorMessage = getAuthErrorMessage(error.code);
            set({ error: errorMessage });
          }
          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Register new user with email and password
      register: async (email: string, password: string, displayName?: string) => {
        try {
          set({ loading: true, error: null });
          const userCredential = await createUserWithEmailAndPassword(auth, email, password);

          // Update profile with display name if provided
          if (displayName && userCredential.user) {
            await updateProfile(userCredential.user, { displayName });
          }

          set({ user: mapFirebaseUser(userCredential.user), isAuthenticated: true });
        } catch (error: any) {
          const errorMessage = getAuthErrorMessage(error.code);
          set({ error: errorMessage });
          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Logout current user
      logout: async () => {
        try {
          set({ loading: true, error: null });
          await signOut(auth);
          set({ user: null, isAuthenticated: false });
        } catch (error: any) {
          const errorMessage = getAuthErrorMessage(error.code);
          set({ error: errorMessage });
          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Send password reset email
      resetPassword: async (email: string) => {
        try {
          set({ loading: true, error: null });
          await sendPasswordResetEmail(auth, email);
        } catch (error: any) {
          const errorMessage = getAuthErrorMessage(error.code);
          set({ error: errorMessage });
          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Force refresh the Firebase ID token
      refreshToken: async () => {
        try {
          const user = auth.currentUser;
          if (user) {
            const token = await user.getIdToken(true); // Force refresh
            return token;
          }
          return null;
        } catch (error) {
          console.error('Failed to refresh token:', error);
          return null;
        }
      },
    }),
    {
      name: 'auth-storage',
      // Only persist user data, not loading/error states
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

/**
 * Initialize Firebase auth state listener.
 *
 * This function sets up a listener that automatically updates the Zustand store
 * whenever Firebase auth state changes (login, logout, token refresh).
 * Call this once when the app starts (in App.tsx).
 */
export const initAuthListener = () => {
  onAuthStateChanged(auth, (user) => {
    useAuthStore.getState().setUser(user);
  });
};

/**
 * Convert Firebase error codes to user-friendly messages.
 * This improves UX by showing clear, actionable error messages.
 */
const getAuthErrorMessage = (errorCode: string): string => {
  switch (errorCode) {
    case 'auth/email-already-in-use':
      return 'This email is already registered.';
    case 'auth/invalid-email':
      return 'Invalid email address.';
    case 'auth/user-disabled':
      return 'This account has been disabled.';
    case 'auth/user-not-found':
      return 'No account found with this email.';
    case 'auth/wrong-password':
      return 'Incorrect password.';
    case 'auth/weak-password':
      return 'Password should be at least 6 characters.';
    case 'auth/too-many-requests':
      return 'Too many failed attempts. Please try again later.';
    case 'auth/network-request-failed':
      return 'Network error. Please check your connection.';
    case 'auth/popup-closed-by-user':
      return 'Sign-in popup was closed before completing.';
    case 'auth/invalid-credential':
      return 'Invalid email or password.';
    default:
      return 'An error occurred. Please try again.';
  }
};
