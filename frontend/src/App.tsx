import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { initAuthListener } from './stores/authStore';
import { ThemeProvider } from './contexts/ThemeContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { TasksPage } from './pages/TasksPage';
import { TodayPage } from './pages/TodayPage';
import { KanbanPage } from './pages/KanbanPage';
import { CalendarPage } from './pages/CalendarPage';
import { AgentPage } from './pages/AgentPage';
import { ProjectsPage } from './pages/ProjectsPage';

/**
 * Main App component with routing and authentication.
 *
 * This component:
 * 1. Initializes the Firebase auth state listener on mount
 * 2. Sets up React Router with public and protected routes
 * 3. Handles route protection using the ProtectedRoute wrapper
 *
 * Routes:
 * - / - Public home page
 * - /login - Login page (public)
 * - /register - Register page (public)
 * - /dashboard - Protected dashboard (requires auth)
 * - /today - Protected today page (smart inbox, requires auth)
 * - /kanban - Protected kanban board (requires auth)
 * - /tasks - Protected tasks page (requires auth)
 */
function App() {
  useEffect(() => {
    // Initialize Firebase auth state listener
    // This keeps the Zustand store in sync with Firebase auth state
    initAuthListener();
  }, []);

  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/today"
            element={
              <ProtectedRoute>
                <TodayPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/kanban"
            element={
              <ProtectedRoute>
                <KanbanPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tasks"
            element={
              <ProtectedRoute>
                <TasksPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/calendar"
            element={
              <ProtectedRoute>
                <CalendarPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <ProjectsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/agent"
            element={
              <ProtectedRoute>
                <AgentPage />
              </ProtectedRoute>
            }
          />

          {/* Catch-all redirect to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
