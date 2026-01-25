import { initializeApp } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';
import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore';

// Firebase configuration from environment variables
// These variables are set in the .env file and accessed via import.meta.env
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

// Validate that required environment variables are present
// This prevents cryptic runtime errors if configuration is missing
const requiredEnvVars = [
  'VITE_FIREBASE_API_KEY',
  'VITE_FIREBASE_AUTH_DOMAIN',
  'VITE_FIREBASE_PROJECT_ID',
];

requiredEnvVars.forEach((varName) => {
  if (!import.meta.env[varName]) {
    throw new Error(`Missing required environment variable: ${varName}`);
  }
});

// Initialize Firebase app
// This creates the Firebase app instance that all other services use
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication
// This is used for login, signup, and token management
export const auth = getAuth(app);

// Initialize Firestore Database
// This is used for storing user data and tasks
export const db = getFirestore(app);

// Optional: Connect to Firebase emulators in development
// Uncomment these lines if you want to use local Firebase emulators for testing
// if (import.meta.env.DEV && import.meta.env.VITE_USE_EMULATORS === 'true') {
//   connectAuthEmulator(auth, 'http://localhost:9099');
//   connectFirestoreEmulator(db, 'localhost', 8080);
//   console.log('Connected to Firebase emulators');
// }

export default app;
