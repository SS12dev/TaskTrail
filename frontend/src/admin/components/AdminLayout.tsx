import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { auth } from '../../../config/firebase';
import { useState, useEffect } from 'react';

export function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [adminEmail, setAdminEmail] = useState('');
  const [adminRole, setAdminRole] = useState('');

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged(async (user) => {
      if (user) {
        setAdminEmail(user.email || '');
        const tokenResult = await user.getIdTokenResult();
        setAdminRole((tokenResult.claims.role as string) || 'unknown');
      }
    });
    return () => unsubscribe();
  }, []);

  const handleLogout = async () => {
    if (confirm('Are you sure you want to logout?')) {
      await auth.signOut();
      navigate('/admin/login');
    }
  };

  const navItems = [
    { path: '/admin/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/admin/users', label: 'Users', icon: '👥' },
    { path: '/admin/analytics', label: 'Analytics', icon: '📈' },
    { path: '/admin/config', label: 'Config', icon: '⚙️' },
    { path: '/admin/audit', label: 'Audit Logs', icon: '📝' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Top Navigation */}
      <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">TaskTrail Admin</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">System Administration</p>
              </div>
            </div>

            {/* User Info */}
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900 dark:text-white">{adminEmail}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 uppercase">{adminRole}</p>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition"
              >
                Logout
              </button>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex space-x-1 mt-4">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    isActive
                      ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <span className="mr-2">{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto">
        <Outlet />
      </main>
    </div>
  );
}
