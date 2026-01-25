import { format, parseISO, isToday, isPast, isFuture, startOfDay, endOfDay } from 'date-fns';

/**
 * Date utility functions for consistent date handling across the app.
 */

/**
 * Format a date to a readable string.
 */
export const formatDate = (date: Date | string | null | undefined, formatStr: string = 'MMM d, yyyy'): string => {
  if (!date) return '';

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return format(dateObj, formatStr);
  } catch {
    return '';
  }
};

/**
 * Format a date with time.
 */
export const formatDateTime = (date: Date | string | null | undefined): string => {
  return formatDate(date, 'MMM d, yyyy h:mm a');
};

/**
 * Check if a date is today.
 */
export const checkIsToday = (date: Date | string | null | undefined): boolean => {
  if (!date) return false;

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return isToday(dateObj);
  } catch {
    return false;
  }
};

/**
 * Check if a date is in the past.
 */
export const checkIsPast = (date: Date | string | null | undefined): boolean => {
  if (!date) return false;

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return isPast(dateObj) && !isToday(dateObj);
  } catch {
    return false;
  }
};

/**
 * Check if a date is in the future.
 */
export const checkIsFuture = (date: Date | string | null | undefined): boolean => {
  if (!date) return false;

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return isFuture(dateObj);
  } catch {
    return false;
  }
};

/**
 * Get start of day for a date.
 */
export const getStartOfDay = (date: Date | string): Date => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return startOfDay(dateObj);
};

/**
 * Get end of day for a date.
 */
export const getEndOfDay = (date: Date | string): Date => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return endOfDay(dateObj);
};

/**
 * Parse ISO string to Date object safely.
 */
export const parseDate = (dateStr: string | null | undefined): Date | null => {
  if (!dateStr) return null;

  try {
    return parseISO(dateStr);
  } catch {
    return null;
  }
};

/**
 * Convert task to calendar event format.
 */
export const taskToCalendarEvent = (task: any) => {
  const dueDate = parseDate(task.dueDate);

  if (!dueDate) return null;

  return {
    id: task.id,
    title: task.title,
    start: dueDate,
    end: dueDate,
    allDay: true,
    resource: task, // Store full task data
  };
};
