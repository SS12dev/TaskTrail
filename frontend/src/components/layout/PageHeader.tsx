import { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: LucideIcon;
  actions?: ReactNode;
  stats?: {
    label: string;
    value: string | number;
    color?: string;
  }[];
}

/**
 * PageHeader - Reusable page header component with icon, title, stats, and actions.
 */
export const PageHeader = ({ title, subtitle, icon: Icon, actions, stats }: PageHeaderProps) => {
  return (
    <div className="bg-white/95 dark:bg-slate-900/95 border-b border-slate-200/60 dark:border-slate-700/60 sticky top-0 z-10 backdrop-blur-sm">
      <div className="px-6 lg:px-8 py-6">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex items-start gap-4 min-w-0 flex-1">
            {Icon && (
              <div className="p-3 bg-linear-to-br from-violet-100 via-purple-100 to-cyan-100 dark:from-violet-950 dark:via-purple-950 dark:to-cyan-950 rounded-xl shadow-sm transition-all hover:scale-105 hover:shadow-md">
                <Icon className="w-7 h-7 text-purple-600 dark:text-purple-400" />
              </div>
            )}
            <div className="min-w-0 flex-1">
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white truncate">{title}</h1>
              {subtitle && (
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400 line-clamp-2">{subtitle}</p>
              )}
            </div>
          </div>
          {actions && <div className="flex items-center gap-3 shrink-0">{actions}</div>}
        </div>

        {stats && stats.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {stats.map((stat, index) => (
              <div
                key={index}
                className="bg-slate-50/50 dark:bg-slate-800/50 rounded-xl px-4 py-3 border border-slate-200/60 dark:border-slate-700/60 hover:border-slate-300 dark:hover:border-slate-600 hover:bg-white dark:hover:bg-slate-800 hover:shadow-sm transition-all duration-200 cursor-default group"
              >
                <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  {stat.label}
                </p>
                <p
                  className={`mt-1 text-2xl font-bold transition-all group-hover:scale-105 ${
                    stat.color || 'text-slate-900 dark:text-white'
                  }`}
                >
                  {stat.value}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
