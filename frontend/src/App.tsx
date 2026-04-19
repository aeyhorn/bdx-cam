import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import { AppShell } from './components/layout/AppShell'
import { RoleGuard } from './components/RoleGuard'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { CasesPage } from './pages/CasesPage'
import { CaseDetailPage } from './pages/CaseDetailPage'
import { NewFeedbackPage } from './pages/NewFeedbackPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { HelpPage } from './pages/HelpPage'
import { SimpleListPage } from './pages/SimpleListPage'
import { Box, CircularProgress } from '@mui/material'

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return <AppShell>{children}</AppShell>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/dashboard"
        element={
          <Protected>
            <DashboardPage />
          </Protected>
        }
      />
      <Route
        path="/feedback/new"
        element={
          <Protected>
            <RoleGuard allow={['FEEDBACK_PRODUCTION']}>
              <NewFeedbackPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/cases/mine"
        element={
          <Protected>
            <RoleGuard allow={['FEEDBACK_PRODUCTION']}>
              <CasesPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/cases"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN', 'ENGINEERING']}>
              <CasesPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/cases/:id"
        element={
          <Protected>
            <CaseDetailPage />
          </Protected>
        }
      />
      <Route
        path="/change-requests"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN', 'ENGINEERING']}>
              <SimpleListPage title="Change Requests" url="/api/v1/change-requests" />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/test-cases"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN', 'ENGINEERING']}>
              <SimpleListPage title="Testfälle" url="/api/v1/test-cases" />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/regression-runs"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN', 'ENGINEERING']}>
              <SimpleListPage title="Regression Runs" url="/api/v1/regression-runs" />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/knowledge"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN', 'ENGINEERING']}>
              <SimpleListPage title="Wissensdatenbank" url="/api/v1/knowledge" />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/users"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <SimpleListPage title="Benutzer" url="/api/v1/users" />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/machines"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <SimpleListPage title="Maschinen" url="/api/v1/machines" />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/control-systems"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <SimpleListPage title="Steuerungen" url="/api/v1/control-systems" />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/post-versions"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <SimpleListPage title="Post-Versionen" url="/api/v1/post-versions" />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/categories"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <SimpleListPage title="Fehlerkategorien" url="/api/v1/categories" />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/statuses"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <SimpleListPage title="Status" url="/api/v1/statuses" />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/severities"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <SimpleListPage title="Severity" url="/api/v1/severities" />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/priorities"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <SimpleListPage title="Priorität" url="/api/v1/priorities" />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/help"
        element={
          <Protected>
            <RoleGuard allow={['FEEDBACK_PRODUCTION']}>
              <HelpPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
