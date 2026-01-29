import { useEffect, useState } from 'react';
import { Folder } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { PageHeader } from '../components/layout/PageHeader';
import { useProjects } from '../hooks/useProjects';
import { ExportDialog } from '../components/ExportDialog';

interface ProjectStats {
  projectId: string;
  messageCount: number;
}

export function ProjectsPage() {
  const { projects, loading, error, createProject, deleteProject } = useProjects();
  const [projectStats, setProjectStats] = useState<Record<string, ProjectStats>>({});
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectColor, setNewProjectColor] = useState('blue');
  const [exportProjectId, setExportProjectId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

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

        {/* Projects Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"></div>
            ))}
          </div>
        ) : projects && projects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <div
                key={project.id}
                className={`rounded-lg border-2 p-6 transition hover:shadow-lg dark:hover:shadow-xl ${colorClasses[project.color as keyof typeof colorClasses] || colorClasses.blue}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-4 h-4 rounded-full ${colorDots[project.color as keyof typeof colorDots] || colorDots.blue}`}></div>
                    <h3 className="font-bold text-lg">{project.name}</h3>
                  </div>
                  <button
                    onClick={() => handleDeleteProject(project.id)}
                    className="text-sm opacity-70 hover:opacity-100 transition"
                  >
                    ✕
                  </button>
                </div>

                {project.description && (
                  <p className="text-sm opacity-75 mb-3">{project.description}</p>
                )}

                <div className="text-xs opacity-75 mb-4">
                  {projectStats[project.id]?.messageCount || 0} messages
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => setExportProjectId(project.id)}
                    className="flex-1 px-3 py-2 text-xs font-medium bg-white/20 hover:bg-white/30 rounded transition"
                  >
                    Export
                  </button>
                  <button className="flex-1 px-3 py-2 text-xs font-medium bg-white/20 hover:bg-white/30 rounded transition">
                    View Tasks
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400 mb-4">No projects yet. Create one to get started!</p>
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
