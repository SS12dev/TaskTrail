import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Calendar,
  CheckCircle2,
  Clock,
  TrendingUp,
  Layers,
  ListTodo,
  ArrowRight,
  Sparkles,
  Zap,
  Target,
  BarChart3,
  Download
} from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { PageHeader } from '../components/layout/PageHeader';
import { MemoryStatsWidget } from '../components/MemoryStatsWidget';
import { ExportDialog } from '../components/ExportDialog';
import { useTasks } from '../hooks/useTasks';

/**
 * DashboardPage - Completely redesigned with modern purple/cyan theme.
 * Features glassmorphism, vibrant gradients, and refined components.
 */
export const DashboardPage = () => {
  const navigate = useNavigate();
  const { tasks, fetchTasks } = useTasks();
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    inProgress: 0,
    todo: 0,
  });
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);

  useEffect(() => {
    fetchTasks({ includeCompleted: true });
  }, [fetchTasks]);

  useEffect(() => {
    setStats({
      total: tasks.length,
      completed: tasks.filter(t => t.status === 'done').length,
      inProgress: tasks.filter(t => t.status === 'in_progress').length,
      todo: tasks.filter(t => t.status === 'todo').length,
    });
  }, [tasks]);

  const completionRate = stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0;

  const quickActions = [
    {
      title: 'Today\'s Focus',
      description: 'View tasks due today and high priority items',
      icon: Calendar,
      gradient: 'from-cyan-500 to-blue-500',
      bgGradient: 'from-cyan-50 to-blue-50',
      iconBg: 'bg-cyan-100',
      iconColor: 'text-cyan-600',
      path: '/today',
    },
    {
      title: 'Kanban Board',
      description: 'Manage tasks with drag and drop interface',
      icon: Layers,
      gradient: 'from-purple-500 to-pink-500',
      bgGradient: 'from-purple-50 to-pink-50',
      iconBg: 'bg-purple-100',
      iconColor: 'text-purple-600',
      path: '/kanban',
    },
    {
      title: 'All Tasks',
      description: 'Browse, filter, and organize all your tasks',
      icon: ListTodo,
      gradient: 'from-violet-500 to-purple-500',
      bgGradient: 'from-violet-50 to-purple-50',
      iconBg: 'bg-violet-100',
      iconColor: 'text-violet-600',
      path: '/tasks',
    },
    {
      title: 'Calendar View',
      description: 'See your tasks in a timeline format',
      icon: CheckCircle2,
      gradient: 'from-indigo-500 to-blue-500',
      bgGradient: 'from-indigo-50 to-blue-50',
      iconBg: 'bg-indigo-100',
      iconColor: 'text-indigo-600',
      path: '/calendar',
    },
  ];

  return (
    <Layout>
      <PageHeader
        title="Dashboard"
        subtitle="Your productivity command center"
        icon={LayoutDashboard}
        stats={[
          { label: 'Total Tasks', value: stats.total, color: 'text-slate-900' },
          { label: 'To Do', value: stats.todo, color: 'text-violet-600' },
          { label: 'In Progress', value: stats.inProgress, color: 'text-cyan-600' },
          { label: 'Completed', value: stats.completed, color: 'text-emerald-600' },
        ]}
      />

      <div className="px-6 lg:px-8 py-8 space-y-8">
        {/* Hero Card with Stats */}
        <div className="relative overflow-hidden rounded-2xl bg-linear-to-br from-purple-600 via-violet-600 to-cyan-600 p-8 shadow-2xl shadow-purple-500/30">
          {/* Decorative background elements */}
          <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10"></div>
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-white/10 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-cyan-400/20 rounded-full blur-3xl"></div>

          <div className="relative z-10">
            <div className="flex items-start justify-between gap-6 mb-8">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-5 h-5 text-cyan-300" />
                  <span className="text-sm font-semibold text-cyan-200 uppercase tracking-wider">Welcome back!</span>
                </div>
                <h2 className="text-3xl font-bold text-white mb-3">
                  You're doing great! 🎉
                </h2>
                <p className="text-purple-100 max-w-2xl">
                  You have {stats.inProgress} tasks in progress and {stats.todo} tasks waiting.
                  Keep up the momentum and make today count!
                </p>
              </div>

              {/* Completion Circle */}
              <div className="hidden lg:flex items-center justify-center w-32 h-32 rounded-full bg-white/10 backdrop-blur-sm border-4 border-white/20 shadow-xl">
                <div className="text-center">
                  <div className="text-3xl font-bold text-white">{completionRate}%</div>
                  <div className="text-xs text-purple-200">Complete</div>
                </div>
              </div>
            </div>

            {/* Quick Stats Row */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-400/20 rounded-lg">
                    <Target className="w-5 h-5 text-emerald-200" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">{stats.completed}</p>
                    <p className="text-sm text-purple-200">Tasks Done</p>
                  </div>
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-cyan-400/20 rounded-lg">
                    <Zap className="w-5 h-5 text-cyan-200" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">{stats.inProgress}</p>
                    <p className="text-sm text-purple-200">Active Now</p>
                  </div>
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-400/20 rounded-lg">
                    <TrendingUp className="w-5 h-5 text-purple-200" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">{stats.todo}</p>
                    <p className="text-sm text-purple-200">Up Next</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions Grid */}
        <div>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-violet-100 dark:bg-violet-950 rounded-lg">
              <Zap className="w-5 h-5 text-violet-600 dark:text-violet-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">Quick Actions</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">Jump to your workspace</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {quickActions.map((action) => {
              const Icon = action.icon;
              return (
                <button
                  key={action.path}
                  onClick={() => navigate(action.path)}
                  className="group relative overflow-hidden bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 text-left"
                >
                  {/* Gradient background on hover */}
                  <div className={`absolute inset-0 bg-linear-to-br ${action.bgGradient} dark:opacity-20 opacity-0 group-hover:opacity-100 transition-opacity duration-200`}></div>

                  <div className="relative flex items-start gap-4">
                    <div className={`${action.iconBg} dark:bg-opacity-20 p-3 rounded-xl group-hover:scale-110 group-hover:rotate-3 transition-all duration-200 shadow-sm`}>
                      <Icon className={`w-6 h-6 ${action.iconColor} dark:brightness-125`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-1">
                        {action.title}
                      </h3>
                      <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-1">
                        {action.description}
                      </p>
                    </div>
                    <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300 group-hover:translate-x-1 transition-all shrink-0" />
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Memory Stats & Export */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <MemoryStatsWidget />
          </div>
          <div className="flex flex-col gap-4">
            <button
              onClick={() => setIsExportDialogOpen(true)}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-linear-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 group"
            >
              <Download className="w-5 h-5 group-hover:scale-110 transition-transform" />
              <span>Export Data</span>
            </button>
          </div>
        </div>

        {/* Activity Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity Card */}
          <div className="lg:col-span-2 bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-indigo-100 dark:bg-indigo-950 rounded-lg">
                <BarChart3 className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Recent Activity</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">Your latest task updates</p>
              </div>
            </div>

            <div className="space-y-3">
              {tasks.slice(0, 5).map((task) => (
                <div
                  key={task.id}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors group"
                >
                  <div className={`w-2 h-2 rounded-full ${
                    task.status === 'done' ? 'bg-emerald-500' :
                    task.status === 'in_progress' ? 'bg-cyan-500' :
                    'bg-violet-500'
                  }`}></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 dark:text-white truncate">{task.title}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{task.status.replace('_', ' ')}</p>
                  </div>
                  <span className="text-xs text-slate-400 dark:text-slate-500">
                    {task.dueDate ? new Date(task.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'No date'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Progress Card */}
          <div className="bg-linear-to-br from-violet-50 to-purple-50 dark:from-violet-950/30 dark:to-purple-950/30 rounded-2xl p-6 border border-violet-200 dark:border-violet-800/50 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-purple-100 dark:bg-purple-950/50 rounded-lg">
                <TrendingUp className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Progress</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">This week's stats</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Completion Rate</span>
                  <span className="text-sm font-bold text-purple-600 dark:text-purple-400">{completionRate}%</span>
                </div>
                <div className="h-2 bg-white dark:bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-linear-to-r from-purple-500 to-cyan-500 rounded-full transition-all duration-500"
                    style={{ width: `${completionRate}%` }}
                  ></div>
                </div>
              </div>

              <div className="pt-4 border-t border-purple-200 dark:border-purple-800/50">
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-slate-600 dark:text-slate-400">Total Tasks</span>
                  <span className="text-sm font-semibold text-slate-900 dark:text-white">{stats.total}</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-slate-600 dark:text-slate-400">Completed</span>
                  <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">{stats.completed}</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-slate-600 dark:text-slate-400">In Progress</span>
                  <span className="text-sm font-semibold text-cyan-600 dark:text-cyan-400">{stats.inProgress}</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-slate-600 dark:text-slate-400">To Do</span>
                  <span className="text-sm font-semibold text-violet-600 dark:text-violet-400">{stats.todo}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <ExportDialog isOpen={isExportDialogOpen} onClose={() => setIsExportDialogOpen(false)} />
    </Layout>
  );
};
