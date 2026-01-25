import api from './api';
import type { Project, ProjectCreateData, ProjectUpdateData } from '../types/project';

/**
 * Project API service.
 * All project-related API calls using the authenticated axios instance.
 */
export const projectApi = {
  /**
   * Get all projects.
   */
  getProjects: async (includeArchived: boolean = false) => {
    const params = new URLSearchParams();
    if (includeArchived) params.append('includeArchived', 'true');

    const response = await api.get(`/api/v1/projects?${params}`);
    return response.data;
  },

  /**
   * Get a single project by ID.
   */
  getProject: async (id: string): Promise<Project> => {
    const response = await api.get(`/api/v1/projects/${id}`);
    return response.data;
  },

  /**
   * Create a new project.
   */
  createProject: async (data: ProjectCreateData): Promise<Project> => {
    const response = await api.post('/api/v1/projects', data);
    return response.data;
  },

  /**
   * Update an existing project.
   */
  updateProject: async (id: string, data: ProjectUpdateData): Promise<Project> => {
    const response = await api.patch(`/api/v1/projects/${id}`, data);
    return response.data;
  },

  /**
   * Delete a project.
   */
  deleteProject: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/projects/${id}`);
  },
};
