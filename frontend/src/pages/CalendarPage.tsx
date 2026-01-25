import { useEffect, useState } from 'react';
import { Calendar as CalendarIcon, Loader2, Plus } from 'lucide-react';
import type { View } from 'react-big-calendar';
import { Layout } from '../components/layout/Layout';
import { PageHeader } from '../components/layout/PageHeader';
import { useTasks } from '../hooks/useTasks';
import { CalendarView } from '../components/calendar/CalendarView';
import { TaskForm } from '../components/tasks/TaskForm';
import type { Task, TaskCreateData } from '../types/task';

/**
 * CalendarPage - Calendar view of tasks by due date.
 * Provides month, week, day, and agenda views.
 */
export const CalendarPage = () => {
  const {
    tasks,
    loading,
    error,
    fetchTasks,
    createTask,
    updateTask,
    deleteTask,
    clearError,
  } = useTasks();

  const [view, setView] = useState<View>('month');
  const [date, setDate] = useState(new Date());
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>(undefined);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(undefined);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch all tasks (including completed) on mount
  useEffect(() => {
    fetchTasks({ includeCompleted: true });
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

  const handleSelectEvent = (task: Task) => {
    setEditingTask(task);
  };

  const handleSelectSlot = (slotInfo: { start: Date; end: Date }) => {
    setSelectedDate(slotInfo.start);
    setIsFormOpen(true);
  };

  const handleCreateTask = async (data: TaskCreateData) => {
    setIsSubmitting(true);
    try {
      // If a date was selected, use it as the due date
      const taskData = selectedDate
        ? { ...data, dueDate: selectedDate.toISOString() }
        : data;

      await createTask(taskData);
      setIsFormOpen(false);
      setSelectedDate(undefined);
      await fetchTasks({ includeCompleted: true });
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
      await fetchTasks({ includeCompleted: true });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelForm = () => {
    setIsFormOpen(false);
    setEditingTask(undefined);
    setSelectedDate(undefined);
  };

  // Count tasks with due dates
  const tasksWithDates = tasks.filter((t) => t.dueDate).length;

  return (
    <Layout>
      <PageHeader
        title="Calendar"
        subtitle="Visualize your tasks in a timeline"
        icon={CalendarIcon}
        stats={[
          { label: 'Scheduled', value: tasksWithDates, color: 'text-cyan-600 dark:text-cyan-400' },
          { label: 'This Week', value: tasks.filter(t => {
            if (!t.dueDate) return false;
            const due = new Date(t.dueDate);
            const now = new Date();
            const weekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
            return due >= now && due <= weekFromNow;
          }).length, color: 'text-purple-600 dark:text-purple-400' },
        ]}
        actions={
          <button
            onClick={() => setIsFormOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-linear-to-r from-violet-600 to-purple-600 text-white rounded-xl hover:shadow-lg hover:scale-105 transition-all duration-200 shadow-sm"
          >
            <Plus className="w-5 h-5" />
            New Task
          </button>
        }
      />

      <div className="px-6 lg:px-8 py-8">

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 rounded-xl">
            <p className="text-sm text-rose-800 dark:text-rose-200">{error}</p>
          </div>
        )}

        {/* Loading state */}
        {loading && tasks.length === 0 ? (
          <div className="flex items-center justify-center py-12 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
            <Loader2 className="w-8 h-8 text-purple-600 dark:text-purple-400 animate-spin" />
          </div>
        ) : (
          <>
            {/* Info banner */}
            <div className="mb-6 p-4 bg-cyan-50 dark:bg-cyan-950/30 border border-cyan-200 dark:border-cyan-800 rounded-xl">
              <div className="flex items-start gap-3">
                <CalendarIcon className="w-5 h-5 text-cyan-600 dark:text-cyan-400 mt-0.5 shrink-0" />
                <div className="text-sm text-cyan-900 dark:text-cyan-100">
                  <p className="font-medium mb-1">Calendar Tips:</p>
                  <ul className="list-disc list-inside space-y-1 text-cyan-800 dark:text-cyan-200">
                    <li>Click on any date to create a new task for that day</li>
                    <li>Click on a task to view and edit details</li>
                    <li>Use the view buttons to switch between Month, Week, Day, and Agenda</li>
                    <li>Tasks are color-coded by priority: Urgent (rose), High (orange), Medium (cyan), Low (slate)</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Calendar */}
            <div style={{ height: '700px' }}>
              <CalendarView
                tasks={tasks}
                onSelectEvent={handleSelectEvent}
                onSelectSlot={handleSelectSlot}
                view={view}
                onViewChange={setView}
                date={date}
                onNavigate={setDate}
              />
            </div>

            {/* Legend */}
            <div className="mt-6 p-4 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3">Legend</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-rose-500 rounded"></div>
                  <span className="text-sm text-slate-700 dark:text-slate-300">Urgent Priority</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-orange-500 rounded"></div>
                  <span className="text-sm text-slate-700 dark:text-slate-300">High Priority</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-cyan-500 rounded"></div>
                  <span className="text-sm text-slate-700 dark:text-slate-300">Medium Priority</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-slate-400 rounded"></div>
                  <span className="text-sm text-slate-700 dark:text-slate-300">Low Priority</span>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">○</span>
                    <span className="text-sm text-slate-700 dark:text-slate-300">To Do</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">◐</span>
                    <span className="text-sm text-slate-700 dark:text-slate-300">In Progress</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">✓</span>
                    <span className="text-sm text-slate-700 dark:text-slate-300">Done</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">⊗</span>
                    <span className="text-sm text-slate-700 dark:text-slate-300">Archived</span>
                  </div>
                </div>
              </div>
            </div>
          </>
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
