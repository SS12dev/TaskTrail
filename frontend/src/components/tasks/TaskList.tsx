import { TaskCard } from './TaskCard';
import type { Task } from '../../types/task';

interface TaskListProps {
  tasks: Task[];
  onEdit: (task: Task) => void;
  onDelete: (taskId: string) => void;
  onTaskClick?: (task: Task) => void;
  emptyMessage?: string;
}

/**
 * TaskList component displays a list of tasks.
 * Shows empty state when no tasks are available.
 */
export const TaskList = ({
  tasks,
  onEdit,
  onDelete,
  onTaskClick,
  emptyMessage = 'No tasks found',
}: TaskListProps) => {
  if (tasks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4">
        <div className="text-center">
          <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-8 h-8 text-slate-400 dark:text-slate-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-1">
            {emptyMessage}
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Get started by creating your first task
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <TaskCard
          key={task.id}
          task={task}
          onEdit={onEdit}
          onDelete={onDelete}
          onClick={onTaskClick}
        />
      ))}
    </div>
  );
};
