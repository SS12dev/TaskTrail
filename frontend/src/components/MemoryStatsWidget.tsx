import { useEffect } from 'react';
import { useMemoryAnalytics } from '../hooks/useMemoryAnalytics';
import { useAuth } from '../hooks/useAuth';

export function MemoryStatsWidget() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { stats, loading, error, fetchStats } = useMemoryAnalytics();

  useEffect(() => {
    if (!isAuthenticated) return;
    fetchStats();
    const interval = setInterval(fetchStats, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [fetchStats, isAuthenticated]);

  if (authLoading) {
    return (
      <div className="rounded-lg bg-linear-to-br from-blue-50 to-indigo-50 dark:from-gray-700 dark:to-gray-800 p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-4 bg-gray-300 rounded w-3/4"></div>
          <div className="h-3 bg-gray-300 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="rounded-lg bg-linear-to-br from-blue-50 to-indigo-50 dark:from-gray-700 dark:to-gray-800 p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-4 bg-gray-300 rounded w-3/4"></div>
          <div className="h-3 bg-gray-300 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4">
        <p className="text-sm text-red-700 dark:text-red-300">Failed to load memory stats</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-linear-to-br from-blue-50 to-indigo-50 dark:from-gray-700 dark:to-gray-800 p-4">
      <div className="space-y-3">
        <div className="flex justify-between items-start">
          <h3 className="font-semibold text-gray-900 dark:text-white">Memory Stats</h3>
          <span className={`text-xs px-2 py-1 rounded ${stats.compaction.status === 'healthy' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'}`}>
            {stats.compaction.status}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <p className="text-gray-600 dark:text-gray-400">Total Messages</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">{stats.messages.total}</p>
          </div>
          <div>
            <p className="text-gray-600 dark:text-gray-400">This Week</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">{stats.messages.past_week}</p>
          </div>
        </div>

        <div className="pt-2 border-t border-gray-200 dark:border-gray-600">
          <p className="text-xs text-gray-600 dark:text-gray-400">{stats.compaction.recommendation}</p>
          {stats.vector_memory.enabled && (
            <p className="text-xs text-green-700 dark:text-green-300 mt-1">✓ Vector memory active</p>
          )}
        </div>
      </div>
    </div>
  );
}
