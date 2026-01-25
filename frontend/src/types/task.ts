/**
 * Task type definitions for TaskTrail.
 * These types match the backend Pydantic models.
 */

export type TaskStatus = "todo" | "in_progress" | "done" | "archived";
export type TaskPriority = "low" | "medium" | "high" | "urgent";
export type RecurrencePattern = "daily" | "weekly" | "monthly" | "yearly";

export interface RecurrenceRule {
  pattern: RecurrencePattern;
  interval: number;
  daysOfWeek?: number[];  // 0=Sunday, 6=Saturday
  endDate?: Date;
  lastGenerated?: Date;
}

export interface Task {
  id: string;
  userId: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  dueDate?: Date;
  tags: string[];
  projectId?: string;
  parentTaskId?: string;
  position: number;
  isRecurring: boolean;
  recurrenceRule?: RecurrenceRule;
  completedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface TaskCreateData {
  title: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  dueDate?: Date;
  tags?: string[];
  projectId?: string;
  parentTaskId?: string;
  isRecurring?: boolean;
  recurrenceRule?: RecurrenceRule;
}

export interface TaskUpdateData {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  dueDate?: Date;
  tags?: string[];
  projectId?: string;
  position?: number;
  isRecurring?: boolean;
  recurrenceRule?: RecurrenceRule;
}

export interface TaskFilters {
  status?: string;
  projectId?: string;
  priority?: string;
  tags?: string[];
  parentTaskId?: string;
  includeCompleted?: boolean;
}
