import { useProjectStore } from '../stores/projectStore';

/**
 * Custom hook to access project state and actions.
 * Provides a clean API for components to interact with projects.
 *
 * This hook wraps the Zustand project store, following the same pattern
 * as the useAuth hook for consistency.
 */
export const useProjects = () => {
  const {
    projects,
    selectedProject,
    loading,
    error,
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    setSelectedProject,
    clearError,
  } = useProjectStore();

  return {
    // State
    projects,
    selectedProject,
    loading,
    error,

    // Actions
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    setSelectedProject,
    clearError,
  };
};
