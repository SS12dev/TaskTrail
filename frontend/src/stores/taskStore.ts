import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Task, TaskCreateData, TaskUpdateData, TaskFilters } from '../types/task';
import { taskApi } from '../services/taskApi';

/**
 * Task store state interface.
 */
interface TaskState {
  tasks: Task[];
  selectedTask: Task | null;
  loading: boolean;
  error: string | null;
}

/**
 * Task store actions interface.
 */
interface TaskActions {
  fetchTasks: (filters?: TaskFilters) => Promise<void>;
  fetchTodayTasks: () => Promise<void>;
  createTask: (data: TaskCreateData) => Promise<Task>;
  updateTask: (id: string, data: TaskUpdateData) => Promise<Task>;
  deleteTask: (id: string) => Promise<void>;
  reorderTask: (id: string, newPosition: number, newStatus?: string) => Promise<void>;
  setSelectedTask: (task: Task | null) => void;
  clearError: () => void;
}

export type TaskStore = TaskState & TaskActions;

/**
 * Zustand store for task state management.
 * Follows the same pattern as authStore with persistence.
 */
export const useTaskStore = create<TaskStore>()(
  persist(
    (set, get) => ({
      // Initial state
      tasks: [],
      selectedTask: null,
      loading: false,
      error: null,

      // Actions
      fetchTasks: async (filters) => {
        set({ loading: true, error: null });
        try {
          const response = await taskApi.getTasks(filters);
          set({ tasks: response.tasks, loading: false });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch tasks';
          set({ error: errorMessage, loading: false });
        }
      },

      fetchTodayTasks: async () => {
        set({ loading: true, error: null });
        try {
          const response = await taskApi.getTodayTasks();
          set({ tasks: response.tasks, loading: false });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch today tasks';
          set({ error: errorMessage, loading: false });
        }
      },

      createTask: async (data) => {
        set({ loading: true, error: null });
        try {
          const task = await taskApi.createTask(data);
          set((state) => ({
            tasks: [...state.tasks, task],
            loading: false,
          }));
          return task;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.message || 'Failed to create task';
          set({ error: errorMessage, loading: false });
          throw error;
        }
      },

      updateTask: async (id, data) => {
        set({ loading: true, error: null });
        try {
          const task = await taskApi.updateTask(id, data);
          set((state) => ({
            tasks: state.tasks.map((t) => (t.id === id ? task : t)),
            selectedTask: state.selectedTask?.id === id ? task : state.selectedTask,
            loading: false,
          }));
          return task;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.message || 'Failed to update task';
          set({ error: errorMessage, loading: false });
          throw error;
        }
      },

      deleteTask: async (id) => {
        set({ loading: true, error: null });
        try {
          await taskApi.deleteTask(id);
          set((state) => ({
            tasks: state.tasks.filter((t) => t.id !== id),
            selectedTask: state.selectedTask?.id === id ? null : state.selectedTask,
            loading: false,
          }));
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.message || 'Failed to delete task';
          set({ error: errorMessage, loading: false });
          throw error;
        }
      },

      reorderTask: async (id, newPosition, newStatus) => {
        try {
          const task = await taskApi.reorderTask(id, newPosition, newStatus);
          set((state) => ({
            tasks: state.tasks.map((t) => (t.id === id ? task : t)),
          }));
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.message || 'Failed to reorder task';
          set({ error: errorMessage });
          throw error;
        }
      },

      setSelectedTask: (task) => set({ selectedTask: task }),
      clearError: () => set({ error: null }),
    }),
    {
      name: 'task-storage',
      partialize: (state) => ({
        // Only persist tasks, not loading/error states
        tasks: state.tasks,
      }),
    }
  )
);
