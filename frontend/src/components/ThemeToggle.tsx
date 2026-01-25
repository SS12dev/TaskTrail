import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

/**
 * ThemeToggle - Beautiful animated toggle switch for dark/light mode.
 * Features smooth slider animation and icon transitions.
 */
export const ThemeToggle = () => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      className="relative inline-flex items-center h-10 w-20 rounded-full transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900 bg-slate-200 dark:bg-slate-700"
      aria-label="Toggle theme"
    >
      {/* Slider */}
      <span
        className={`inline-block h-8 w-8 transform rounded-full bg-white dark:bg-slate-900 shadow-lg transition-transform duration-300 ease-in-out ${
          isDark ? 'translate-x-11' : 'translate-x-1'
        }`}
      >
        {/* Icon inside slider */}
        <span className="flex items-center justify-center h-full">
          {isDark ? (
            <Moon className="w-4 h-4 text-purple-500 animate-in fade-in zoom-in duration-200" />
          ) : (
            <Sun className="w-4 h-4 text-amber-500 animate-in fade-in zoom-in duration-200" />
          )}
        </span>
      </span>

      {/* Background icons */}
      <span className="absolute left-2 top-1/2 -translate-y-1/2">
        <Sun className={`w-4 h-4 transition-opacity duration-300 ${isDark ? 'opacity-40' : 'opacity-0'} text-amber-400`} />
      </span>
      <span className="absolute right-2 top-1/2 -translate-y-1/2">
        <Moon className={`w-4 h-4 transition-opacity duration-300 ${isDark ? 'opacity-0' : 'opacity-40'} text-slate-400`} />
      </span>
    </button>
  );
};
