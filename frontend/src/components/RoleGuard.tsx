import { Navigate } from 'react-router-dom'
import { useAuth, type RoleKey } from '../context/AuthContext'
import { Box, CircularProgress } from '@mui/material'

export function RoleGuard({
  allow,
  children,
}: {
  allow: RoleKey[]
  children: React.ReactNode
}) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  if (!allow.includes(user.role.key)) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}
