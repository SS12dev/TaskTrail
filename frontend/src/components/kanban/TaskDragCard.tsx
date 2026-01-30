import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Calendar, Tag, Trash2, Edit2, GripVertical } from 'lucide-react';
import type { Task } from '../../types/task';

interface TaskDragCardProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (taskId: string) => void;
}

/**
 * TaskDragCard - Draggable task card for Kanban board.
 * Similar to TaskCard but with drag and drop capabilities.
 */
export const TaskDragCard = ({ task, onEdit, onDelete }: TaskDragCardProps) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  // Priority color mapping
  const priorityColors = {
    low: 'bg-gray-100 text-gray-700',
    medium: 'bg-blue-100 text-blue-700',
    high: 'bg-orange-100 text-orange-700',
    urgent: 'bg-red-100 text-red-700',
  };

  // Format due date
  const formatDueDate = (date?: Date) => {
    if (!date) return null;
    const dueDate = new Date(date);
    const today = new Date();
    const diffDays = Math.ceil((dueDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

    if (task.status === 'done' || task.status === 'archived') {
      return { text: dueDate.toLocaleDateString(), color: 'bg-gray-100 text-gray-700' };
    }

    if (diffDays < 0) return { text: 'Overdue', color: 'bg-red-100 text-red-700' };
    if (diffDays === 0) return { text: 'Today', color: 'bg-blue-100 text-blue-700' };
    if (diffDays === 1) return { text: 'Tomorrow', color: 'bg-green-100 text-green-700' };
    return { text: dueDate.toLocaleDateString(), color: 'bg-gray-100 text-gray-700' };
  };

  const dueDateInfo = formatDueDate(task.dueDate);

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-3 hover:shadow-md transition-shadow group"
    >
      {/* Header: Drag handle + Title + Actions */}
      <div className="flex items-start gap-2 mb-2">
        {/* Drag handle */}
        <button
          {...attributes}
          {...listeners}
          className="mt-1 text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity"
          aria-label="Drag task"
        >
          <GripVertical className="w-4 h-4" />
        </button>

        {/* Title */}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 text-sm line-clamp-2">
            {task.title}
          </h3>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit(task);
            }}
            className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
            aria-label="Edit task"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(task.id);
            }}
            className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
            aria-label="Delete task"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Description */}
      {task.description && (
        <p className="text-xs text-gray-600 mb-2 line-clamp-2 ml-6">
          {task.description}
        </p>
      )}

      {/* Metadata: Priority, Due Date, Tags */}
      <div className="flex flex-wrap items-center gap-1.5 ml-6">
        {/* Priority badge */}
        <span
          className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
            priorityColors[task.priority]
          }`}
        >
          {task.priority}
        </span>

        {/* Due date badge */}
        {dueDateInfo && (
          <span
            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium ${dueDateInfo.color}`}
          >
            <Calendar className="w-3 h-3" />
            {dueDateInfo.text}
          </span>
        )}

        {/* Tags */}
        {task.tags.length > 0 && (
          <>
            {task.tags.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium"
              >
                <Tag className="w-3 h-3" />
                {tag}
              </span>
            ))}
            {task.tags.length > 2 && (
              <span className="text-xs text-gray-500">
                +{task.tags.length - 2}
              </span>
            )}
          </>
        )}
      </div>
    </div>
  );
};
