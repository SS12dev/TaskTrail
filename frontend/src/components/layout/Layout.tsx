import { ReactNode } from 'react';
import { Sidebar } from './Sidebar';

interface LayoutProps {
  children: ReactNode;
}

/**
 * Layout - Main layout wrapper with sidebar navigation.
 * Provides consistent layout across all protected pages.
 */
export const Layout = ({ children }: LayoutProps) => {
  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-950">
        <div className="min-h-full">
          {children}
        </div>
      </main>
    </div>
  );
};
