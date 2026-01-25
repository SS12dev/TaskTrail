import type { Task } from '../../types/task';

interface TaskCalendarEventProps {
  event: {
    title: string;
    resource: Task;
  };
}

/**
 * TaskCalendarEvent - Custom event renderer for calendar.
 * Shows task with priority color coding.
 */
export const TaskCalendarEvent = ({ event }: TaskCalendarEventProps) => {
  const task = event.resource;

  // Priority color mapping
  const priorityColors: Record<string, string> = {
    urgent: 'bg-red-500 text-white',
    high: 'bg-orange-500 text-white',
    medium: 'bg-blue-500 text-white',
    low: 'bg-gray-400 text-white',
  };

  const colorClass = priorityColors[task.priority] || 'bg-gray-400 text-white';

  // Status indicator
  const statusIcons: Record<string, string> = {
    todo: '○',
    in_progress: '◐',
    done: '✓',
    archived: '⊗',
  };

  const statusIcon = statusIcons[task.status] || '○';

  return (
    <div className={`px-2 py-1 rounded text-xs font-medium truncate ${colorClass}`}>
      <span className="mr-1">{statusIcon}</span>
      {event.title}
    </div>
  );
};
