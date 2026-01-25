import api from './api';
import type { Task, TaskCreateData, TaskUpdateData, TaskFilters } from '../types/task';

/**
 * Convert task dates from string to Date objects.
 * The backend sends ISO date strings that need to be converted to JS Date objects.
 */
function parseTasks(data: any): any {
  if (!data) return data;
  
  if (Array.isArray(data)) {
    return data.map(item => parseTaskDates(item));
  }
  
  return parseTaskDates(data);
}

function parseTaskDates(obj: any): any {
  if (!obj) return obj;
  
  const result = { ...obj };
  
  // Parse date fields
  if (result.dueDate && typeof result.dueDate === 'string') {
    result.dueDate = new Date(result.dueDate);
  }
  if (result.createdAt && typeof result.createdAt === 'string') {
    result.createdAt = new Date(result.createdAt);
  }
  if (result.updatedAt && typeof result.updatedAt === 'string') {
    result.updatedAt = new Date(result.updatedAt);
  }
  if (result.completedAt && typeof result.completedAt === 'string') {
    result.completedAt = new Date(result.completedAt);
  }
  
  // Parse nested task arrays if they exist
  if (result.tasks && Array.isArray(result.tasks)) {
    result.tasks = result.tasks.map((task: any) => parseTaskDates(task));
  }
  
  return result;
}

/**
 * Task API service.
 * All task-related API calls using the authenticated axios instance.
 */
export const taskApi = {
  /**
   * Get all tasks with optional filters.
   */
  getTasks: async (filters?: TaskFilters) => {
    const params = new URLSearchParams();

    if (filters?.status) params.append('status', filters.status);
    if (filters?.projectId) params.append('projectId', filters.projectId);
    if (filters?.priority) params.append('priority', filters.priority);
    if (filters?.parentTaskId) params.append('parentTaskId', filters.parentTaskId);
    if (filters?.includeCompleted) params.append('includeCompleted', 'true');
    if (filters?.tags) {
      filters.tags.forEach(tag => params.append('tags', tag));
    }

    const queryString = params.toString();
    const response = await api.get(`/api/v1/tasks/${queryString ? `?${queryString}` : ''}`);
    return parseTasks(response.data);
  },

  /**
   * Get tasks for the "Today" page (smart inbox).
   */
  getTodayTasks: async () => {
    const response = await api.get('/api/v1/tasks/today/');
    return parseTasks(response.data);
  },

  /**
   * Get a single task by ID.
   */
  getTask: async (id: string): Promise<Task> => {
    const response = await api.get(`/api/v1/tasks/${id}/`);
    return parseTaskDates(response.data);
  },

  /**
   * Create a new task.
   */
  createTask: async (data: TaskCreateData): Promise<Task> => {
    const response = await api.post('/api/v1/tasks/', data);
    return parseTaskDates(response.data);
  },

  /**
   * Update an existing task.
   */
  updateTask: async (id: string, data: TaskUpdateData): Promise<Task> => {
    const response = await api.patch(`/api/v1/tasks/${id}/`, data);
    return parseTaskDates(response.data);
  },

  /**
   * Delete a task.
   */
  deleteTask: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/tasks/${id}/`);
  },

  /**
   * Reorder a task (for drag & drop).
   */
  reorderTask: async (
    id: string,
    newPosition: number,
    newStatus?: string
  ): Promise<Task> => {
    const params = new URLSearchParams();
    params.append('newPosition', newPosition.toString());
    if (newStatus) params.append('newStatus', newStatus);

    const response = await api.post(`/api/v1/tasks/${id}/reorder/?${params}`);
    return parseTaskDates(response.data);
  },
};
