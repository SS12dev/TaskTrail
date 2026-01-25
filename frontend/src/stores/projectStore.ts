import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Project, ProjectCreateData, ProjectUpdateData } from '../types/project';
import { projectApi } from '../services/projectApi';

/**
 * Project store state interface.
 */
interface ProjectState {
  projects: Project[];
  selectedProject: Project | null;
  loading: boolean;
  error: string | null;
}

/**
 * Project store actions interface.
 */
interface ProjectActions {
  fetchProjects: (includeArchived?: boolean) => Promise<void>;
  createProject: (data: ProjectCreateData) => Promise<Project>;
  updateProject: (id: string, data: ProjectUpdateData) => Promise<Project>;
  deleteProject: (id: string) => Promise<void>;
  setSelectedProject: (project: Project | null) => void;
  clearError: () => void;
}

export type ProjectStore = ProjectState & ProjectActions;

/**
 * Zustand store for project state management.
 * Follows the same pattern as taskStore with persistence.
 */
export const useProjectStore = create<ProjectStore>()(
  persist(
    (set, get) => ({
      // Initial state
      projects: [],
      selectedProject: null,
      loading: false,
      error: null,

      // Actions
      fetchProjects: async (includeArchived = false) => {
        set({ loading: true, error: null });
        try {
          const response = await projectApi.getProjects(includeArchived);
          set({ projects: response.projects, loading: false });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch projects';
          set({ error: errorMessage, loading: false });
        }
      },

      createProject: async (data) => {
        set({ loading: true, error: null });
        try {
          const project = await projectApi.createProject(data);
          set((state) => ({
            projects: [...state.projects, project],
            loading: false,
          }));
          return project;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.message || 'Failed to create project';
          set({ error: errorMessage, loading: false });
          throw error;
        }
      },

      updateProject: async (id, data) => {
        set({ loading: true, error: null });
        try {
          const project = await projectApi.updateProject(id, data);
          set((state) => ({
            projects: state.projects.map((p) => (p.id === id ? project : p)),
            selectedProject: state.selectedProject?.id === id ? project : state.selectedProject,
            loading: false,
          }));
          return project;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.message || 'Failed to update project';
          set({ error: errorMessage, loading: false });
          throw error;
        }
      },

      deleteProject: async (id) => {
        set({ loading: true, error: null });
        try {
          await projectApi.deleteProject(id);
          set((state) => ({
            projects: state.projects.filter((p) => p.id !== id),
            selectedProject: state.selectedProject?.id === id ? null : state.selectedProject,
            loading: false,
          }));
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.message || 'Failed to delete project';
          set({ error: errorMessage, loading: false });
          throw error;
        }
      },

      setSelectedProject: (project) => set({ selectedProject: project }),
      clearError: () => set({ error: null }),
    }),
    {
      name: 'project-storage',
      partialize: (state) => ({
        // Only persist projects, not loading/error states
        projects: state.projects,
      }),
    }
  )
);
