import { useEffect, useState } from 'react';
import { Loader2, Layers, AlertCircle } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { PageHeader } from '../components/layout/PageHeader';
import { useTasks } from '../hooks/useTasks';
import { KanbanBoard } from '../components/kanban/KanbanBoard';
import { TaskForm } from '../components/tasks/TaskForm';
import type { Task, TaskCreateData, TaskStatus } from '../types/task';

/**
 * KanbanPage - Kanban board view with drag and drop.
 * Displays tasks in three columns: To Do, In Progress, Done.
 */
export const KanbanPage = () => {
  const {
    tasks,
    loading,
    error,
    fetchTasks,
    createTask,
    updateTask,
    deleteTask,
    reorderTask,
    clearError,
  } = useTasks();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>(undefined);
  const [newTaskStatus, setNewTaskStatus] = useState<TaskStatus>('todo');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch tasks on mount (exclude completed to focus on active work)
  useEffect(() => {
    fetchTasks({ includeCompleted: false });
  }, [fetchTasks]);

  // Clear error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const handleAddTask = (status: TaskStatus) => {
    setNewTaskStatus(status);
    setIsFormOpen(true);
  };

  const handleCreateTask = async (data: TaskCreateData) => {
    setIsSubmitting(true);
    try {
      await createTask({ ...data, status: newTaskStatus });
      setIsFormOpen(false);
      await fetchTasks({ includeCompleted: false });
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
      await fetchTasks({ includeCompleted: false });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      await deleteTask(taskId);
      await fetchTasks({ includeCompleted: false });
    }
  };

  const handleEditClick = (task: Task) => {
    setEditingTask(task);
  };

  const handleReorder = async (taskId: string, newPosition: number, newStatus: TaskStatus) => {
    await reorderTask(taskId, newPosition, newStatus);
    await fetchTasks({ includeCompleted: false });
  };

  const handleCancelForm = () => {
    setIsFormOpen(false);
    setEditingTask(undefined);
  };

  const todoCount = tasks.filter(t => t.status === 'todo').length;
  const inProgressCount = tasks.filter(t => t.status === 'in_progress').length;
  const doneCount = tasks.filter(t => t.status === 'done').length;

  return (
    <Layout>
      <PageHeader
        title="Kanban Board"
        subtitle="Organize and track your tasks with drag and drop"
        icon={Layers}
        stats={[
          { label: 'Total Active', value: tasks.length, color: 'text-gray-900' },
          { label: 'To Do', value: todoCount, color: 'text-gray-600' },
          { label: 'In Progress', value: inProgressCount, color: 'text-blue-600' },
          { label: 'Done', value: doneCount, color: 'text-green-600' },
        ]}
      />

      <div className="h-[calc(100vh-13rem)] px-6 lg:px-8 py-6 overflow-x-auto">
        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Loading state */}
        {loading && tasks.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Loading your board...</p>
            </div>
          </div>
        ) : (
          <div>
            <KanbanBoard
              tasks={tasks}
              onEdit={handleEditClick}
              onDelete={handleDeleteTask}
              onAddTask={handleAddTask}
              onReorder={handleReorder}
            />
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
