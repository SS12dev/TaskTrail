import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Calendar,
  CheckSquare,
  Layers,
  ListTodo,
  LogOut,
  Menu,
  X,
  Sparkles,
  User,
  Zap,
  Bot
} from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { ThemeToggle } from '../ThemeToggle';

/**
 * Sidebar - Modern navigation sidebar with new design system.
 * Supports both light and dark themes with vibrant purple/cyan accents.
 */
export const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/today', icon: Calendar, label: 'Today' },
    { path: '/kanban', icon: Layers, label: 'Kanban' },
    { path: '/tasks', icon: ListTodo, label: 'All Tasks' },
    { path: '/calendar', icon: CheckSquare, label: 'Calendar' },
    { path: '/agent', icon: Bot, label: 'AI Agent' },
  ];

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const NavLink = ({ item }: { item: typeof navItems[0] }) => {
    const isActive = location.pathname === item.path;
    const Icon = item.icon;

    return (
      <Link
        to={item.path}
        onClick={() => setIsMobileMenuOpen(false)}
        className={`group relative flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
          isActive
            ? 'bg-linear-to-r from-violet-600 to-purple-600 text-white shadow-lg shadow-purple-500/30'
            : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100/80 dark:hover:bg-slate-800/50 hover:text-slate-900 dark:hover:text-white'
        }`}
      >
        <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-500 dark:text-slate-400 group-hover:text-violet-600 dark:group-hover:text-violet-400'} transition-colors`} />
        <span className="font-medium text-sm">{item.label}</span>
        {isActive && (
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-linear-to-b from-purple-400 to-cyan-400 rounded-r-full shadow-lg shadow-purple-400/50" />
        )}
      </Link>
    );
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-3 bg-linear-to-br from-purple-600 to-indigo-600 rounded-xl shadow-lg hover:shadow-xl transition-all hover:scale-105"
      >
        {isMobileMenuOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <Menu className="w-6 h-6 text-white" />
        )}
      </button>

      {/* Overlay for mobile */}
      {isMobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 transition-opacity"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-40 w-72 bg-white dark:bg-slate-900 border-r border-slate-200/60 dark:border-slate-700/60 transform transition-transform duration-300 ease-in-out ${
          isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 py-6 border-b border-slate-200/60 dark:border-slate-700/60">
            <div className="relative">
              <div className="w-10 h-10 bg-linear-to-br from-purple-500 via-violet-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/40">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full border-2 border-white dark:border-slate-900 animate-pulse"></div>
            </div>
            <div>
              <span className="text-lg font-bold bg-linear-to-r from-purple-600 to-cyan-600 bg-clip-text text-transparent">
                TaskTrail
              </span>
              <span className="block text-xs text-slate-500 dark:text-slate-400 font-medium">Workspace</span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            {navItems.map((item) => (
              <NavLink key={item.path} item={item} />
            ))}
          </nav>

          {/* User Section */}
          <div className="border-t border-slate-200/60 dark:border-slate-700/60 p-4 bg-slate-50/50 dark:bg-slate-800/50">
            <div className="flex items-center gap-3 px-4 py-3 mb-3 bg-linear-to-r from-violet-50 via-purple-50 to-cyan-50 dark:from-violet-950/30 dark:via-purple-950/30 dark:to-cyan-950/30 rounded-xl border border-purple-100/50 dark:border-purple-800/50 shadow-sm">
              <div className="w-9 h-9 bg-linear-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center ring-2 ring-white dark:ring-slate-800 shadow-md">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                  {user?.displayName || 'User'}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{user?.email}</p>
              </div>
            </div>

            {/* Theme Toggle */}
            <div className="mb-3 flex justify-center">
              <ThemeToggle />
            </div>

            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-xl transition-all duration-200 hover:shadow-sm group border border-transparent hover:border-rose-200 dark:hover:border-rose-800"
            >
              <LogOut className="w-4 h-4 group-hover:scale-110 transition-transform" />
              <span className="font-medium text-sm">Logout</span>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
