import { Calendar, Tag, Trash2, Edit2, Circle, CheckCircle2, Clock } from 'lucide-react';
import type { Task } from '../../types/task';

interface TaskCardProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (taskId: string) => void;
  onClick?: (task: Task) => void;
}

/**
 * TaskCard component displays a single task with all its information.
 * Modern design with purple/cyan theme and dark mode support.
 */
export const TaskCard = ({ task, onEdit, onDelete, onClick }: TaskCardProps) => {
  // Priority color mapping with dark mode
  const priorityColors = {
    low: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300',
    medium: 'bg-cyan-100 dark:bg-cyan-950/50 text-cyan-700 dark:text-cyan-300',
    high: 'bg-orange-100 dark:bg-orange-950/50 text-orange-700 dark:text-orange-300',
    urgent: 'bg-rose-100 dark:bg-rose-950/50 text-rose-700 dark:text-rose-300',
  };

  // Status icon mapping with modern colors
  const statusIcons = {
    todo: <Circle className="w-5 h-5 text-violet-400 dark:text-violet-500" />,
    in_progress: <Clock className="w-5 h-5 text-cyan-500 dark:text-cyan-400" />,
    done: <CheckCircle2 className="w-5 h-5 text-emerald-500 dark:text-emerald-400" />,
    archived: <Circle className="w-5 h-5 text-slate-400 dark:text-slate-600" />,
  };

  // Format due date with modern colors
  const formatDueDate = (date?: Date) => {
    if (!date) return null;
    const dueDate = new Date(date);
    const today = new Date();
    const diffDays = Math.ceil((dueDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

    if (task.status === 'done' || task.status === 'archived') {
      return { text: dueDate.toLocaleDateString(), color: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300' };
    }

    if (diffDays < 0) return { text: 'Overdue', color: 'bg-rose-100 dark:bg-rose-950/50 text-rose-700 dark:text-rose-300' };
    if (diffDays === 0) return { text: 'Today', color: 'bg-cyan-100 dark:bg-cyan-950/50 text-cyan-700 dark:text-cyan-300' };
    if (diffDays === 1) return { text: 'Tomorrow', color: 'bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300' };
    return { text: dueDate.toLocaleDateString(), color: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300' };
  };

  const dueDateInfo = formatDueDate(task.dueDate);

  return (
    <div
      className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-4 hover:shadow-lg hover:border-purple-300 dark:hover:border-purple-700 transition-all duration-200 cursor-pointer group"
      onClick={() => onClick?.(task)}
    >
      {/* Header: Status icon + Title + Actions */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="mt-0.5 shrink-0">
            {statusIcons[task.status]}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-slate-900 dark:text-white truncate">
              {task.title}
            </h3>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit(task);
            }}
            className="p-1.5 text-slate-400 dark:text-slate-500 hover:text-purple-600 dark:hover:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-950/30 rounded-lg transition-colors"
            aria-label="Edit task"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(task.id);
            }}
            className="p-1.5 text-slate-400 dark:text-slate-500 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-lg transition-colors"
            aria-label="Delete task"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Description */}
      {task.description && (
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-3 line-clamp-2">
          {task.description}
        </p>
      )}

      {/* Metadata: Priority, Due Date, Tags */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Priority badge */}
        <span
          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
            priorityColors[task.priority]
          }`}
        >
          {task.priority}
        </span>

        {/* Due date badge */}
        {dueDateInfo && (
          <span
            className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${dueDateInfo.color}`}
          >
            <Calendar className="w-3 h-3" />
            {dueDateInfo.text}
          </span>
        )}

        {/* Tags */}
        {task.tags.length > 0 && (
          <>
            {task.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 dark:bg-purple-950/50 text-purple-700 dark:text-purple-300 rounded-full text-xs font-medium"
              >
                <Tag className="w-3 h-3" />
                {tag}
              </span>
            ))}
            {task.tags.length > 3 && (
              <span className="text-xs text-slate-500 dark:text-slate-400">
                +{task.tags.length - 3} more
              </span>
            )}
          </>
        )}
      </div>
    </div>
  );
};
