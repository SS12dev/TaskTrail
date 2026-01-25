import { useTaskStore } from '../stores/taskStore';

/**
 * Custom hook to access task state and actions.
 * Provides a clean API for components to interact with tasks.
 *
 * This hook wraps the Zustand task store, following the same pattern
 * as the useAuth hook for consistency.
 */
export const useTasks = () => {
  const {
    tasks,
    selectedTask,
    loading,
    error,
    fetchTasks,
    fetchTodayTasks,
    createTask,
    updateTask,
    deleteTask,
    reorderTask,
    setSelectedTask,
    clearError,
  } = useTaskStore();

  return {
    // State
    tasks,
    selectedTask,
    loading,
    error,

    // Actions
    fetchTasks,
    fetchTodayTasks,
    createTask,
    updateTask,
    deleteTask,
    reorderTask,
    setSelectedTask,
    clearError,
  };
};
