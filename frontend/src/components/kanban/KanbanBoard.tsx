import { DndContext, DragOverlay, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import type { DragEndEvent, DragOverEvent, DragStartEvent } from '@dnd-kit/core';
import { arrayMove } from '@dnd-kit/sortable';
import { useState } from 'react';
import { KanbanColumn } from './KanbanColumn';
import { TaskDragCard } from './TaskDragCard';
import type { Task, TaskStatus } from '../../types/task';

interface KanbanBoardProps {
  tasks: Task[];
  onEdit: (task: Task) => void;
  onDelete: (taskId: string) => void;
  onAddTask: (status: TaskStatus) => void;
  onReorder: (taskId: string, newPosition: number, newStatus: TaskStatus) => void;
}

/**
 * KanbanBoard - Main drag and drop board component.
 * Manages three columns: To Do, In Progress, Done.
 */
export const KanbanBoard = ({
  tasks,
  onEdit,
  onDelete,
  onAddTask,
  onReorder,
}: KanbanBoardProps) => {
  const [activeTask, setActiveTask] = useState<Task | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement required before drag starts
      },
    })
  );

  // Categorize tasks by status
  const todoTasks = tasks.filter((t) => t.status === 'todo');
  const inProgressTasks = tasks.filter((t) => t.status === 'in_progress');
  const doneTasks = tasks.filter((t) => t.status === 'done');

  const getTasksByStatus = (status: TaskStatus): Task[] => {
    switch (status) {
      case 'todo':
        return todoTasks;
      case 'in_progress':
        return inProgressTasks;
      case 'done':
        return doneTasks;
      default:
        return [];
    }
  };

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const task = tasks.find((t) => t.id === active.id);
    if (task) {
      setActiveTask(task);
    }
  };

  const handleDragOver = (event: DragOverEvent) => {
    // This handles the visual feedback while dragging
    // The actual reordering happens in handleDragEnd
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over) {
      setActiveTask(null);
      return;
    }

    const activeTask = tasks.find((t) => t.id === active.id);
    if (!activeTask) {
      setActiveTask(null);
      return;
    }

    // Determine the new status
    const overId = over.id as string;
    let newStatus: TaskStatus;

    // Check if dropped on a column
    if (overId === 'todo' || overId === 'in_progress' || overId === 'done') {
      newStatus = overId as TaskStatus;
    } else {
      // Dropped on another task - use that task's status
      const overTask = tasks.find((t) => t.id === overId);
      newStatus = overTask?.status || activeTask.status;
    }

    // Get tasks in the target column
    const targetColumnTasks = getTasksByStatus(newStatus);

    // Calculate new position
    let newPosition: number;

    if (overId === newStatus) {
      // Dropped on the column itself (empty area) - put at end
      newPosition = targetColumnTasks.length;
    } else {
      // Dropped on another task
      const overTask = tasks.find((t) => t.id === overId);
      if (overTask && overTask.status === newStatus) {
        // Dropped on a task in the same column
        const overIndex = targetColumnTasks.findIndex((t) => t.id === overId);
        newPosition = overIndex;
      } else {
        // Dropped on a task in a different column - put at end
        newPosition = targetColumnTasks.length;
      }
    }

    // Only reorder if something changed
    if (activeTask.status !== newStatus || activeTask.position !== newPosition) {
      onReorder(activeTask.id, newPosition, newStatus);
    }

    setActiveTask(null);
  };

  const handleDragCancel = () => {
    setActiveTask(null);
  };

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className="flex gap-6 overflow-x-auto pb-4">
        <KanbanColumn
          title="To Do"
          status="todo"
          tasks={todoTasks}
          onEdit={onEdit}
          onDelete={onDelete}
          onAddTask={onAddTask}
          color="bg-gray-400"
        />
        <KanbanColumn
          title="In Progress"
          status="in_progress"
          tasks={inProgressTasks}
          onEdit={onEdit}
          onDelete={onDelete}
          onAddTask={onAddTask}
          color="bg-blue-500"
        />
        <KanbanColumn
          title="Done"
          status="done"
          tasks={doneTasks}
          onEdit={onEdit}
          onDelete={onDelete}
          onAddTask={onAddTask}
          color="bg-green-500"
        />
      </div>

      {/* Drag overlay - shows the dragged task */}
      <DragOverlay>
        {activeTask ? (
          <div className="rotate-3 scale-105">
            <TaskDragCard
              task={activeTask}
              onEdit={() => {}}
              onDelete={() => {}}
            />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
};
