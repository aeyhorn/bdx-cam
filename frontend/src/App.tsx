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
import { WorkflowPage } from './pages/WorkflowPage'
import { UsersAdminPage } from './pages/admin/UsersAdminPage'
import { MachinesAdminPage } from './pages/admin/MachinesAdminPage'
import { ControlSystemsAdminPage } from './pages/admin/ControlSystemsAdminPage'
import { PostVersionsAdminPage } from './pages/admin/PostVersionsAdminPage'
import { CamStepModelsAdminPage } from './pages/admin/CamStepModelsAdminPage'
import { MachinePostBindingsAdminPage } from './pages/admin/MachinePostBindingsAdminPage'
import { CategoriesAdminPage } from './pages/admin/CategoriesAdminPage'
import { StatusesAdminPage } from './pages/admin/StatusesAdminPage'
import { SystemBuildsAdminPage } from './pages/admin/SystemBuildsAdminPage'
import { PrioritiesListPage, SeveritiesListPage } from './pages/admin/LookupReadonlyPage'
import { ChangeRequestsPage } from './pages/engineering/ChangeRequestsPage'
import { TestCasesPage } from './pages/engineering/TestCasesPage'
import { KnowledgePage } from './pages/engineering/KnowledgePage'
import { RegressionRunsPage } from './pages/engineering/RegressionRunsPage'
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

const allRoles = ['ADMIN', 'ENGINEERING', 'FEEDBACK_PRODUCTION'] as const

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
        path="/workflow"
        element={
          <Protected>
            <RoleGuard allow={[...allRoles]}>
              <WorkflowPage />
            </RoleGuard>
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
              <ChangeRequestsPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/test-cases"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN', 'ENGINEERING']}>
              <TestCasesPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/regression-runs"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN', 'ENGINEERING']}>
              <RegressionRunsPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/knowledge"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN', 'ENGINEERING']}>
              <KnowledgePage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/users"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <UsersAdminPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/machines"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <MachinesAdminPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/control-systems"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <ControlSystemsAdminPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/post-versions"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <PostVersionsAdminPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/cam-step-models"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <CamStepModelsAdminPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/machine-post-bindings"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <MachinePostBindingsAdminPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/system-builds"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <SystemBuildsAdminPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/categories"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <CategoriesAdminPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/statuses"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <StatusesAdminPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/severities"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <SeveritiesListPage />
            </RoleGuard>
          </Protected>
        }
      />
      <Route
        path="/admin/priorities"
        element={
          <Protected>
            <RoleGuard allow={['ADMIN']}>
              <PrioritiesListPage />
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
