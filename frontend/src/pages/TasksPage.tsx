import { useEffect, useState } from 'react';
import { Plus, Loader2, Filter, X, ListTodo, AlertCircle } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { PageHeader } from '../components/layout/PageHeader';
import { useTasks } from '../hooks/useTasks';
import { TaskList } from '../components/tasks/TaskList';
import { TaskForm } from '../components/tasks/TaskForm';
import type { Task, TaskCreateData, TaskStatus, TaskPriority } from '../types/task';

/**
 * TasksPage - Enhanced page to view and manage all tasks with filters.
 * Displays all tasks with filtering options for better management.
 */
export const TasksPage = () => {
  const {
    tasks,
    loading,
    error,
    fetchTasks,
    createTask,
    updateTask,
    deleteTask,
    clearError,
  } = useTasks();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>(undefined);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Filter states
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all');
  const [priorityFilter, setPriorityFilter] = useState<TaskPriority | 'all'>('all');
  const [includeCompleted, setIncludeCompleted] = useState(true);

  // Fetch tasks on mount and when filters change
  useEffect(() => {
    const filters: any = {};
    if (statusFilter !== 'all') filters.status = statusFilter;
    if (priorityFilter !== 'all') filters.priority = priorityFilter;
    filters.includeCompleted = includeCompleted;

    fetchTasks(filters);
  }, [statusFilter, priorityFilter, includeCompleted, fetchTasks]);

  // Clear error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const handleCreateTask = async (data: TaskCreateData) => {
    setIsSubmitting(true);
    try {
      await createTask(data);
      setIsFormOpen(false);
      // Refresh with current filters
      const filters: any = {};
      if (statusFilter !== 'all') filters.status = statusFilter;
      if (priorityFilter !== 'all') filters.priority = priorityFilter;
      filters.includeCompleted = includeCompleted;
      await fetchTasks(filters);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateTask = async (data: TaskCreateData) => {
    if (!editingTask) return;
    setIsSubmitting(true);
    try {
      await updateTask(editingTask.id, data);
      setEditingTask(undefined);
      // Refresh with current filters
      const filters: any = {};
      if (statusFilter !== 'all') filters.status = statusFilter;
      if (priorityFilter !== 'all') filters.priority = priorityFilter;
      filters.includeCompleted = includeCompleted;
      await fetchTasks(filters);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      await deleteTask(taskId);
      // Refresh with current filters
      const filters: any = {};
      if (statusFilter !== 'all') filters.status = statusFilter;
      if (priorityFilter !== 'all') filters.priority = priorityFilter;
      filters.includeCompleted = includeCompleted;
      await fetchTasks(filters);
    }
  };

  const handleEditClick = (task: Task) => {
    setEditingTask(task);
  };

  const handleCancelForm = () => {
    setIsFormOpen(false);
    setEditingTask(undefined);
  };

  const clearAllFilters = () => {
    setStatusFilter('all');
    setPriorityFilter('all');
    setIncludeCompleted(true);
  };

  const hasActiveFilters = statusFilter !== 'all' || priorityFilter !== 'all' || !includeCompleted;

  return (
    <Layout>
      <PageHeader
        title="All Tasks"
        subtitle="Browse, filter, and manage all your tasks"
        icon={ListTodo}
        stats={[
          { label: 'Total Tasks', value: tasks.length, color: 'text-gray-900' },
        ]}
        actions={
          <>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                showFilters || hasActiveFilters
                  ? 'bg-purple-600 text-white hover:bg-purple-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Filter className="w-5 h-5" />
              Filters
              {hasActiveFilters && (
                <span className="px-2 py-0.5 bg-white/20 rounded-full text-xs font-medium">
                  Active
                </span>
              )}
            </button>
            <button
              onClick={() => setIsFormOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
            >
              <Plus className="w-5 h-5" />
              New Task
            </button>
          </>
        }
      />

      <div className="px-6 lg:px-8 py-8">
        {/* Filters Panel */}
        {showFilters && (
          <div className="mb-6 p-6 bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Filters</h3>
              {hasActiveFilters && (
                <button
                  onClick={clearAllFilters}
                  className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  <X className="w-4 h-4" />
                  Clear all
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as TaskStatus | 'all')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                >
                  <option value="all">All Statuses</option>
                  <option value="todo">To Do</option>
                  <option value="in_progress">In Progress</option>
                  <option value="done">Done</option>
                  <option value="archived">Archived</option>
                </select>
              </div>

              {/* Priority Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority
                </label>
                <select
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value as TaskPriority | 'all')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                >
                  <option value="all">All Priorities</option>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              {/* Include Completed */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Completed Tasks
                </label>
                <label className="flex items-center space-x-3 px-3 py-2 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 bg-white">
                  <input
                    type="checkbox"
                    checked={includeCompleted}
                    onChange={(e) => setIncludeCompleted(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-gray-700">Include completed</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Active filter badges */}
        {hasActiveFilters && (
          <div className="mb-4 flex flex-wrap gap-2">
            {statusFilter !== 'all' && (
              <span className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium flex items-center gap-2">
                Status: {statusFilter.replace('_', ' ')}
                <button onClick={() => setStatusFilter('all')} className="hover:bg-blue-200 rounded p-0.5">
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
            {priorityFilter !== 'all' && (
              <span className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded-lg text-sm font-medium flex items-center gap-2">
                Priority: {priorityFilter}
                <button onClick={() => setPriorityFilter('all')} className="hover:bg-purple-200 rounded p-0.5">
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
            {!includeCompleted && (
              <span className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium flex items-center gap-2">
                Excluding completed
                <button onClick={() => setIncludeCompleted(true)} className="hover:bg-gray-200 rounded p-0.5">
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Loading state */}
        {loading && tasks.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Loading your tasks...</p>
            </div>
          </div>
        ) : (
          <>
            {/* Task count */}
            <div className="mb-4">
              <p className="text-sm text-gray-600">
                {tasks.length} {tasks.length === 1 ? 'task' : 'tasks'}
                {hasActiveFilters && ' (filtered)'}
              </p>
            </div>

            {/* Task list */}
            <TaskList
              tasks={tasks}
              onEdit={handleEditClick}
              onDelete={handleDeleteTask}
              emptyMessage={hasActiveFilters ? 'No tasks match your filters' : 'No tasks yet'}
            />
          </>
        )}

        {/* Task form modal */}
        {(isFormOpen || editingTask) && (
          <TaskForm
            task={editingTask}
            onSubmit={editingTask ? handleUpdateTask : handleCreateTask}
            onCancel={handleCancelForm}
            isLoading={isSubmitting}
          />
        )}
      </div>
    </Layout>
  );
};
