import { Calendar, dateFnsLocalizer } from 'react-big-calendar';
import type { View } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import { enUS } from 'date-fns/locale';
import { TaskCalendarEvent } from './TaskCalendarEvent';
import type { Task } from '../../types/task';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import './calendar-custom.css';

const locales = {
  'en-US': enUS,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

interface CalendarViewProps {
  tasks: Task[];
  onSelectEvent: (task: Task) => void;
  onSelectSlot?: (slotInfo: { start: Date; end: Date }) => void;
  view: View;
  onViewChange: (view: View) => void;
  date: Date;
  onNavigate: (date: Date) => void;
}

/**
 * CalendarView - Wrapper for react-big-calendar with task events.
 * Displays tasks on their due dates with customization.
 */
export const CalendarView = ({
  tasks,
  onSelectEvent,
  onSelectSlot,
  view,
  onViewChange,
  date,
  onNavigate,
}: CalendarViewProps) => {
  // Convert tasks to calendar events
  const events = tasks
    .filter((task) => task.dueDate)
    .map((task) => ({
      id: task.id,
      title: task.title,
      start: new Date(task.dueDate!),
      end: new Date(task.dueDate!),
      allDay: true,
      resource: task,
    }));

  return (
    <div className="h-full bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <Calendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        style={{ height: '100%', minHeight: 600 }}
        view={view}
        onView={onViewChange}
        date={date}
        onNavigate={onNavigate}
        onSelectEvent={(event) => onSelectEvent(event.resource)}
        onSelectSlot={onSelectSlot}
        selectable
        components={{
          event: TaskCalendarEvent,
        }}
        eventPropGetter={(event) => {
          const task = event.resource as Task;
          const priorityColors: Record<string, string> = {
            urgent: '#ef4444',
            high: '#f97316',
            medium: '#3b82f6',
            low: '#9ca3af',
          };

          return {
            style: {
              backgroundColor: priorityColors[task.priority] || '#9ca3af',
              borderRadius: '4px',
              opacity: task.status === 'done' ? 0.6 : 1,
              border: 'none',
            },
          };
        }}
        views={['month', 'week', 'day', 'agenda']}
        popup
        showMultiDayTimes
        step={60}
        timeslots={1}
      />
    </div>
  );
};
