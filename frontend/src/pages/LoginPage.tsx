import { LoginForm } from '../components/auth/LoginForm';

/**
 * LoginPage - Public page for user login.
 *
 * This page wraps the LoginForm component in a nice layout
 * with a gradient background.
 */
export const LoginPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <LoginForm />
    </div>
  );
};
