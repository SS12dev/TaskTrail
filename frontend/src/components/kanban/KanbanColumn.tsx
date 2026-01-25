import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { Plus } from 'lucide-react';
import { TaskDragCard } from './TaskDragCard';
import type { Task, TaskStatus } from '../../types/task';

interface KanbanColumnProps {
  title: string;
  status: TaskStatus;
  tasks: Task[];
  onEdit: (task: Task) => void;
  onDelete: (taskId: string) => void;
  onAddTask: (status: TaskStatus) => void;
  color: string;
}

/**
 * KanbanColumn - Droppable column for Kanban board.
 * Contains draggable task cards.
 */
export const KanbanColumn = ({
  title,
  status,
  tasks,
  onEdit,
  onDelete,
  onAddTask,
  color,
}: KanbanColumnProps) => {
  const { setNodeRef, isOver } = useDroppable({
    id: status,
  });

  return (
    <div className="flex flex-col bg-gray-50 rounded-lg p-4 min-h-[600px] w-80">
      {/* Column header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${color}`} />
          <h2 className="font-semibold text-gray-900">
            {title}
            <span className="ml-2 text-sm font-normal text-gray-500">
              {tasks.length}
            </span>
          </h2>
        </div>
        <button
          onClick={() => onAddTask(status)}
          className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded transition-colors"
          aria-label={`Add task to ${title}`}
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* Droppable area */}
      <div
        ref={setNodeRef}
        className={`flex-1 space-y-3 transition-colors rounded-lg p-2 ${
          isOver ? 'bg-blue-50 border-2 border-blue-300 border-dashed' : ''
        }`}
      >
        <SortableContext
          items={tasks.map((t) => t.id)}
          strategy={verticalListSortingStrategy}
        >
          {tasks.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-sm text-gray-400">
              Drop tasks here
            </div>
          ) : (
            tasks.map((task) => (
              <TaskDragCard
                key={task.id}
                task={task}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))
          )}
        </SortableContext>
      </div>
    </div>
  );
};
