import { RegisterForm } from '../components/auth/RegisterForm';

/**
 * RegisterPage - Public page for user registration.
 *
 * This page wraps the RegisterForm component in a nice layout
 * with a gradient background.
 */
export const RegisterPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <RegisterForm />
    </div>
  );
};
