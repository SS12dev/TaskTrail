import { useEffect, useState } from 'react';
import { Plus, Calendar, AlertCircle, Flame, Loader2 } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { PageHeader } from '../components/layout/PageHeader';
import { useTasks } from '../hooks/useTasks';
import { TaskList } from '../components/tasks/TaskList';
import { TaskForm } from '../components/tasks/TaskForm';
import type { Task, TaskCreateData } from '../types/task';

/**
 * TodayPage - Smart inbox showing the most important tasks.
 * Displays three sections: Overdue, Due Today, and High Priority.
 */
export const TodayPage = () => {
  const { tasks, loading, error, fetchTodayTasks, createTask, updateTask, deleteTask, clearError } = useTasks();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>(undefined);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch today's tasks on mount
  useEffect(() => {
    fetchTodayTasks();
  }, [fetchTodayTasks]);

  // Clear error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  // Categorize tasks
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const overdueTasks = tasks.filter((task) => {
    if (!task.dueDate) return false;
    const dueDate = new Date(task.dueDate);
    dueDate.setHours(0, 0, 0, 0);
    return dueDate < today;
  });

  const dueTodayTasks = tasks.filter((task) => {
    if (!task.dueDate) return false;
    const dueDate = new Date(task.dueDate);
    dueDate.setHours(0, 0, 0, 0);
    return dueDate.getTime() === today.getTime();
  });

  const highPriorityTasks = tasks.filter((task) => {
    const isHighPriority = task.priority === 'high' || task.priority === 'urgent';
    const isNotOverdueOrDueToday = !overdueTasks.includes(task) && !dueTodayTasks.includes(task);
    return isHighPriority && isNotOverdueOrDueToday;
  });

  const handleCreateTask = async (data: TaskCreateData) => {
    setIsSubmitting(true);
    try {
      await createTask(data);
      setIsFormOpen(false);
      await fetchTodayTasks();
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
      await fetchTodayTasks();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      await deleteTask(taskId);
      await fetchTodayTasks();
    }
  };

  const handleEditClick = (task: Task) => {
    setEditingTask(task);
  };

  const handleCancelForm = () => {
    setIsFormOpen(false);
    setEditingTask(undefined);
  };

  const totalTasks = overdueTasks.length + dueTodayTasks.length + highPriorityTasks.length;

  return (
    <Layout>
      <PageHeader
        title="Today"
        subtitle="Focus on what matters most right now"
        icon={Calendar}
        stats={[
          { label: 'Total Focus', value: totalTasks, color: 'text-slate-900 dark:text-white' },
          { label: 'Overdue', value: overdueTasks.length, color: 'text-rose-600 dark:text-rose-400' },
          { label: 'Due Today', value: dueTodayTasks.length, color: 'text-cyan-600 dark:text-cyan-400' },
          { label: 'High Priority', value: highPriorityTasks.length, color: 'text-orange-600 dark:text-orange-400' },
        ]}
        actions={
          <button
            onClick={() => setIsFormOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-linear-to-r from-violet-600 to-purple-600 text-white rounded-xl hover:shadow-lg hover:scale-105 transition-all duration-200 shadow-sm"
          >
            <Plus className="w-5 h-5" />
            New Task
          </button>
        }
      />

      <div className="px-6 lg:px-8 py-8">
        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 rounded-xl flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
            <p className="text-sm text-rose-800 dark:text-rose-200">{error}</p>
          </div>
        )}

        {/* Loading state */}
        {loading && tasks.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-purple-600 dark:text-purple-400 animate-spin mx-auto mb-4" />
              <p className="text-slate-600 dark:text-slate-400">Loading your tasks...</p>
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Overdue Tasks */}
            {overdueTasks.length > 0 && (
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-rose-50 dark:bg-rose-950/30 rounded-xl">
                    <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Overdue</h2>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{overdueTasks.length} tasks need immediate attention</p>
                  </div>
                </div>
                <TaskList
                  tasks={overdueTasks}
                  onEdit={handleEditClick}
                  onDelete={handleDeleteTask}
                  emptyMessage="No overdue tasks"
                />
              </section>
            )}

            {/* Due Today */}
            {dueTodayTasks.length > 0 && (
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-cyan-50 dark:bg-cyan-950/30 rounded-xl">
                    <Calendar className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Due Today</h2>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{dueTodayTasks.length} tasks to complete today</p>
                  </div>
                </div>
                <TaskList
                  tasks={dueTodayTasks}
                  onEdit={handleEditClick}
                  onDelete={handleDeleteTask}
                  emptyMessage="No tasks due today"
                />
              </section>
            )}

            {/* High Priority */}
            {highPriorityTasks.length > 0 && (
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-orange-50 dark:bg-orange-950/30 rounded-xl">
                    <Flame className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">High Priority</h2>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{highPriorityTasks.length} important tasks</p>
                  </div>
                </div>
                <TaskList
                  tasks={highPriorityTasks}
                  onEdit={handleEditClick}
                  onDelete={handleDeleteTask}
                  emptyMessage="No high priority tasks"
                />
              </section>
            )}

            {/* Empty state */}
            {totalTasks === 0 && !loading && (
              <div className="text-center py-20">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-emerald-50 dark:bg-emerald-950/30 rounded-full mb-6">
                  <Calendar className="w-10 h-10 text-emerald-600 dark:text-emerald-400" />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">All Clear!</h3>
                <p className="text-slate-600 dark:text-slate-400 mb-6 max-w-md mx-auto">
                  You don't have any urgent tasks right now. Great job staying on top of things!
                </p>
                <button
                  onClick={() => setIsFormOpen(true)}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-linear-to-r from-violet-600 to-purple-600 text-white rounded-xl hover:shadow-lg hover:scale-105 transition-all duration-200"
                >
                  <Plus className="w-5 h-5" />
                  Create New Task
                </button>
              </div>
            )}
          </div>
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
