/**
 * Project type definitions for TaskTrail.
 * These types match the backend Pydantic models.
 */

export interface Project {
  id: string;
  userId: string;
  name: string;
  description: string;
  color: string;  // Hex color
  icon: string;   // Lucide icon name
  isArchived: boolean;
  taskCount?: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface ProjectCreateData {
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  isArchived?: boolean;
}

export interface ProjectUpdateData {
  name?: string;
  description?: string;
  color?: string;
  icon?: string;
  isArchived?: boolean;
}
