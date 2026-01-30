import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { initAuthListener } from '../stores/authStore';
import { ThemeProvider } from '../contexts/ThemeContext';
import { AdminLoginPage } from './pages/AdminLoginPage';
import { AdminDashboardPage } from './pages/AdminDashboardPage';
import { UserManagementPage } from './pages/UserManagementPage';
import { AdminLayout } from './components/AdminLayout';

function AdminApp() {
  useEffect(() => {
    initAuthListener();
  }, []);

  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          {/* Login */}
          <Route path="/admin/login" element={<AdminLoginPage />} />
          
          {/* Admin Routes */}
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<AdminDashboardPage />} />
            <Route path="users" element={<UserManagementPage />} />
            <Route path="analytics" element={<div className="p-6"><h1 className="text-2xl font-bold">Analytics Coming Soon</h1></div>} />
            <Route path="config" element={<div className="p-6"><h1 className="text-2xl font-bold">Configuration Coming Soon</h1></div>} />
            <Route path="audit" element={<div className="p-6"><h1 className="text-2xl font-bold">Audit Logs Coming Soon</h1></div>} />
          </Route>

          {/* Redirect root to login */}
          <Route path="*" element={<Navigate to="/admin/login" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default AdminApp;
