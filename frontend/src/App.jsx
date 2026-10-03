import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import AuthPage from './pages/AuthPage'
import DashboardPage from './pages/DashboardPage'

function ProtectedRoute({ children }) {
  return localStorage.getItem('access_token') ? children : <Navigate to="/" replace />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AuthPage />} />
        <Route path="/forgot-password" element={<AuthPage />} />
        <Route path="/reset-password" element={<AuthPage />} />
        <Route path="/complete-profile" element={<ProtectedRoute><AuthPage /></ProtectedRoute>} />
        <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/librarian" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/books" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/my-loans" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/my-requests" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/notifications" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
