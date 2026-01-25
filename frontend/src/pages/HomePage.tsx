import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

/**
 * HomePage - Public landing page.
 *
 * Features:
 * - Welcome message
 * - Navigation to login/register or dashboard based on auth state
 * - Simple, clean design with Tailwind CSS
 */
export const HomePage: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-linear-to-br from-blue-50 to-indigo-100">
      {/* Navigation */}
      <nav className="p-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">TaskTrail</h1>
          <div className="space-x-4">
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-4 py-2 text-blue-600 hover:text-blue-700 font-medium"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-20 text-center">
        <h2 className="text-5xl font-bold mb-6 text-gray-900">
          Welcome to TaskTrail
        </h2>
        <p className="text-xl text-gray-700 mb-8">
          Your personal task management solution with secure authentication.
        </p>
        {!isAuthenticated && (
          <Link
            to="/register"
            className="inline-block px-8 py-3 bg-blue-600 text-white text-lg rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Get Started
          </Link>
        )}
      </main>
    </div>
  );
};
