import axios from 'axios';
import { auth } from '../config/firebase';

/**
 * Axios instance configured for TaskTrail API.
 *
 * This instance automatically:
 * 1. Adds the Firebase ID token to all requests via Authorization header
 * 2. Handles token expiration by refreshing and retrying failed requests
 * 3. Points to the backend API URL from environment variables
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000, // 10 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor to add Firebase authentication token.
 *
 * This runs before every request and automatically adds the current
 * user's Firebase ID token to the Authorization header.
 * The backend will verify this token to authenticate the request.
 */
api.interceptors.request.use(
  async (config) => {
    try {
      const user = auth.currentUser;
      if (user) {
        // Get the ID token from Firebase (Firebase handles caching)
        const token = await user.getIdToken();
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Failed to get auth token:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for error handling and token refresh.
 *
 * This intercepts failed requests and handles specific error cases:
 * - 401 Unauthorized: Attempts to refresh the token and retry the request
 * - Other errors: Passes them through for component-level handling
 */
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 errors (token expired or invalid)
    // Only retry once to avoid infinite loops
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const user = auth.currentUser;
        if (user) {
          // Force token refresh
          const newToken = await user.getIdToken(true);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          // Retry the original request with the new token
          return api(originalRequest);
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        // Token refresh failed - user needs to re-authenticate
        // The ProtectedRoute component will handle redirecting to login
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
