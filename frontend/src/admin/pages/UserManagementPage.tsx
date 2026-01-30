import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getAllUsers, UserSummary, suspendUser, unsuspendUser, updateUserTier, deleteUser } from '../services/adminApi';

export function UserManagementPage() {
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [tierFilter, setTierFilter] = useState('');
  const [suspendedFilter, setSuspendedFilter] = useState<boolean | undefined>(undefined);

  useEffect(() => {
    loadUsers();
  }, [page, searchQuery, tierFilter, suspendedFilter]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await getAllUsers({
        page,
        page_size: 20,
        search: searchQuery || undefined,
        tier: tierFilter || undefined,
        suspended: suspendedFilter,
      });
      setUsers(response.users);
      setTotalPages(Math.ceil(response.total / response.page_size));
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSuspend = async (userId: string) => {
    if (!confirm('Are you sure you want to suspend this user?')) return;
    
    try {
      const reason = prompt('Enter suspension reason:');
      if (!reason) return;
      
      await suspendUser(userId, reason);
      loadUsers();
    } catch (err: any) {
      alert(`Failed to suspend user: ${err.message}`);
    }
  };

  const handleUnsuspend = async (userId: string) => {
    if (!confirm('Are you sure you want to unsuspend this user?')) return;
    
    try {
      await unsuspendUser(userId);
      loadUsers();
    } catch (err: any) {
      alert(`Failed to unsuspend user: ${err.message}`);
    }
  };

  const handleTierUpdate = async (userId: string, currentTier: string) => {
    const newTier = prompt(`Enter new tier (current: ${currentTier}):`, currentTier);
    if (!newTier || newTier === currentTier) return;
    
    try {
      await updateUserTier(userId, newTier);
      loadUsers();
    } catch (err: any) {
      alert(`Failed to update tier: ${err.message}`);
    }
  };

  const handleDelete = async (userId: string, email: string) => {
    const confirmation = prompt(`Type "${email}" to confirm deletion:`);
    if (confirmation !== email) {
      alert('Deletion cancelled - email did not match');
      return;
    }
    
    try {
      await deleteUser(userId);
      loadUsers();
    } catch (err: any) {
      alert(`Failed to delete user: ${err.message}`);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">User Management</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Manage user accounts and permissions</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Search</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              placeholder="Search by email..."
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Tier</label>
            <select
              value={tierFilter}
              onChange={(e) => {
                setTierFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">All Tiers</option>
              <option value="free">Free</option>
              <option value="pro">Pro</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Status</label>
            <select
              value={suspendedFilter === undefined ? '' : suspendedFilter ? 'suspended' : 'active'}
              onChange={(e) => {
                setSuspendedFilter(e.target.value === '' ? undefined : e.target.value === 'suspended');
                setPage(1);
              }}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">All Users</option>
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => {
                setSearchQuery('');
                setTierFilter('');
                setSuspendedFilter(undefined);
                setPage(1);
              }}
              className="w-full px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Users Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading users...</p>
          </div>
        ) : users.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-gray-600 dark:text-gray-400">No users found</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">User</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tasks/Projects</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tokens</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tier</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {users.map((user) => (
                    <tr key={user.uid} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white">{user.display_name || 'No name'}</div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">{user.email}</div>
                          <div className="text-xs text-gray-400 dark:text-gray-500">{user.uid}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {user.task_count} / {user.project_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {user.total_tokens_used.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleTierUpdate(user.uid, user.current_tier)}
                          className="px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 hover:bg-blue-200 dark:hover:bg-blue-800 transition"
                        >
                          {user.current_tier}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {user.is_suspended ? (
                          <span className="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                            Suspended
                          </span>
                        ) : (
                          <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                            Active
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                        <Link
                          to={`/admin/users/${user.uid}`}
                          className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300"
                        >
                          View
                        </Link>
                        {user.is_suspended ? (
                          <button
                            onClick={() => handleUnsuspend(user.uid)}
                            className="text-green-600 dark:text-green-400 hover:text-green-900 dark:hover:text-green-300"
                          >
                            Unsuspend
                          </button>
                        ) : (
                          <button
                            onClick={() => handleSuspend(user.uid)}
                            className="text-orange-600 dark:text-orange-400 hover:text-orange-900 dark:hover:text-orange-300"
                          >
                            Suspend
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(user.uid, user.email)}
                          className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-600"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-600"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
