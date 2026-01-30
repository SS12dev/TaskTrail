import { useState, useEffect } from 'react';
import { Folder, CheckCircle2, Circle, Clock } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { PageHeader } from '../components/layout/PageHeader';
import { useProjects } from '../hooks/useProjects';
import { useTasks } from '../hooks/useTasks';
import { ExportDialog } from '../components/ExportDialog';

export function ProjectsPage() {
  const { projects, loading, error, createProject, deleteProject, fetchProjects } = useProjects();
  const { tasks, fetchTasks } = useTasks();
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectColor, setNewProjectColor] = useState('blue');
  const [exportProjectId, setExportProjectId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());

  // Fetch projects and tasks on mount
  useEffect(() => {
    fetchProjects();
    fetchTasks();
  }, [fetchProjects, fetchTasks]);

  // Group tasks by project
  const tasksByProject = tasks.reduce((acc, task) => {
    const projectId = task.projectId || 'unassigned';
    if (!acc[projectId]) acc[projectId] = [];
    acc[projectId].push(task);
    return acc;
  }, {} as Record<string, typeof tasks>);

  const toggleProjectExpansion = (projectId: string) => {
    setExpandedProjects(prev => {
      const next = new Set(prev);
      if (next.has(projectId)) {
        next.delete(projectId);
      } else {
        next.add(projectId);
      }
      return next;
    });
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;

    setIsCreating(true);
    try {
      await createProject({
        name: newProjectName,
        color: newProjectColor,
        description: '',
      });
      setNewProjectName('');
      setNewProjectColor('blue');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (!window.confirm('Are you sure you want to delete this project?')) return;
    await deleteProject(projectId);
  };

  const colorClasses = {
    blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-700',
    red: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-300 dark:border-red-700',
    green: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-300 dark:border-green-700',
    purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-purple-300 dark:border-purple-700',
    orange: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border-orange-300 dark:border-orange-700',
  };

  const colorDots = {
    blue: 'bg-blue-500',
    red: 'bg-red-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
  };

  return (
    <Layout>
      <PageHeader
        title="Projects"
        subtitle="Organize and track all your projects with memory insights"
        icon={Folder}
        stats={[
          { label: 'Total Projects', value: projects.length, color: 'text-slate-900 dark:text-white' },
        ]}
      />

      <div className="px-6 lg:px-8 py-8">

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded-lg">
            {error}
          </div>
        )}

        {/* Create New Project */}
        <div className="mb-8 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Create New Project</h2>
          <div className="flex gap-3 flex-wrap">
            <input
              type="text"
              placeholder="Project name..."
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleCreateProject()}
              className="flex-1 min-w-48 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 outline-none"
            />
            <select
              value={newProjectColor}
              onChange={(e) => setNewProjectColor(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 outline-none"
            >
              <option value="blue">Blue</option>
              <option value="red">Red</option>
              <option value="green">Green</option>
              <option value="purple">Purple</option>
              <option value="orange">Orange</option>
            </select>
            <button
              onClick={handleCreateProject}
              disabled={!newProjectName.trim() || isCreating}
              className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {isCreating ? 'Creating...' : 'Create'}
            </button>
          </div>
        </div>

        {/* Projects List */}
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"></div>
            ))}
          </div>
        ) : projects && projects.length > 0 ? (
          <div className="space-y-4">
            {projects.map((project) => {
              const projectTasks = tasksByProject[project.id] || [];
              const isExpanded = expandedProjects.has(project.id);
              const completedCount = projectTasks.filter(t => t.status === 'done').length;
              const totalCount = projectTasks.length;

              return (
                <div
                  key={project.id}
                  className={`rounded-lg border-2 transition hover:shadow-lg dark:hover:shadow-xl ${colorClasses[project.color as keyof typeof colorClasses] || colorClasses.blue}`}
                >
                  {/* Project Header */}
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <button
                        onClick={() => toggleProjectExpansion(project.id)}
                        className="flex items-center gap-3 flex-1 text-left group"
                      >
                        <div className={`w-4 h-4 rounded-full ${colorDots[project.color as keyof typeof colorDots] || colorDots.blue}`}></div>
                        <h3 className="font-bold text-lg">{project.name}</h3>
                        <span className="text-sm opacity-75">
                          ({completedCount}/{totalCount} tasks)
                        </span>
                        <span className="ml-auto text-sm opacity-50 group-hover:opacity-100 transition">
                          {isExpanded ? '▼' : '▶'}
                        </span>
                      </button>
                      <button
                        onClick={() => handleDeleteProject(project.id)}
                        className="text-sm opacity-70 hover:opacity-100 transition ml-4"
                      >
                        ✕
                      </button>
                    </div>

                    {project.description && (
                      <p className="text-sm opacity-75 mb-3 ml-7">{project.description}</p>
                    )}

                    <div className="flex gap-2 ml-7">
                      <button
                        onClick={() => setExportProjectId(project.id)}
                        className="px-3 py-2 text-xs font-medium bg-white/20 hover:bg-white/30 rounded transition"
                      >
                        Export
                      </button>
                    </div>
                  </div>

                  {/* Tasks List (Collapsible) */}
                  {isExpanded && projectTasks.length > 0 && (
                    <div className="px-6 pb-6 space-y-2">
                      <div className="border-t border-current/20 pt-4">
                        <h4 className="text-sm font-semibold mb-3 opacity-75">Tasks:</h4>
                        {projectTasks.map((task) => (
                          <div
                            key={task.id}
                            className="flex items-center gap-3 p-3 bg-white/10 dark:bg-black/10 rounded-lg"
                          >
                            {task.status === 'done' ? (
                              <CheckCircle2 className="w-4 h-4 shrink-0 text-green-600 dark:text-green-400" />
                            ) : task.status === 'in_progress' ? (
                              <Clock className="w-4 h-4 shrink-0 text-yellow-600 dark:text-yellow-400" />
                            ) : (
                              <Circle className="w-4 h-4 shrink-0 opacity-50" />
                            )}
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium truncate">{task.title}</div>
                              {task.description && (
                                <div className="text-xs opacity-75 truncate">{task.description}</div>
                              )}
                            </div>
                            <div className="text-xs opacity-75 shrink-0">
                              {task.priority === 'high' && '🔴'}
                              {task.priority === 'medium' && '🟡'}
                              {task.priority === 'low' && '🟢'}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* No tasks message */}
                  {isExpanded && projectTasks.length === 0 && (
                    <div className="px-6 pb-6">
                      <div className="border-t border-current/20 pt-4">
                        <p className="text-sm opacity-75 italic">
                          No tasks yet. Ask the AI agent to create tasks for this project!
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            <Folder className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>No projects yet. Create your first project above!</p>
          </div>
        )}
      </div>

      <ExportDialog
        isOpen={exportProjectId !== null}
        onClose={() => setExportProjectId(null)}
        projectId={exportProjectId || undefined}
      />
    </Layout>
  );
}
