import {
  Box,
  Divider,
  Drawer,
  List,
  ListItemButton,
  ListItemText,
  Toolbar,
  Typography,
  AppBar,
  IconButton,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth, type RoleKey } from '../../context/AuthContext'

const drawerWidth = 260

type NavItem = { to: string; label: string; roles: RoleKey[] }

const navItems: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', roles: ['ADMIN', 'ENGINEERING', 'FEEDBACK_PRODUCTION'] },
  { to: '/feedback/new', label: 'Neues Feedback', roles: ['FEEDBACK_PRODUCTION'] },
  { to: '/cases/mine', label: 'Meine Fälle', roles: ['FEEDBACK_PRODUCTION'] },
  { to: '/cases', label: 'Alle Fälle', roles: ['ADMIN', 'ENGINEERING'] },
  { to: '/change-requests', label: 'Change Requests', roles: ['ADMIN', 'ENGINEERING'] },
  { to: '/test-cases', label: 'Testfälle', roles: ['ADMIN', 'ENGINEERING'] },
  { to: '/regression-runs', label: 'Regressionen', roles: ['ADMIN', 'ENGINEERING'] },
  { to: '/knowledge', label: 'Wissensdatenbank', roles: ['ADMIN', 'ENGINEERING'] },
  { to: '/admin/users', label: 'Benutzer', roles: ['ADMIN'] },
  { to: '/admin/machines', label: 'Maschinen', roles: ['ADMIN'] },
  { to: '/admin/control-systems', label: 'Steuerungen', roles: ['ADMIN'] },
  { to: '/admin/post-versions', label: 'Post-Versionen', roles: ['ADMIN'] },
  { to: '/admin/categories', label: 'Kategorien', roles: ['ADMIN'] },
  { to: '/admin/statuses', label: 'Status', roles: ['ADMIN'] },
  { to: '/admin/severities', label: 'Severity', roles: ['ADMIN'] },
  { to: '/admin/priorities', label: 'Priorität', roles: ['ADMIN'] },
  { to: '/help', label: 'Hilfe', roles: ['FEEDBACK_PRODUCTION'] },
]

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const loc = useLocation()
  const navigate = useNavigate()
  const theme = useTheme()
  const isSm = useMediaQuery(theme.breakpoints.down('md'))
  const [open, setOpen] = useState(false)

  const role = user?.role.key
  const items = navItems.filter((i) => role && i.roles.includes(role))

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Toolbar>
        <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
          CAM Feedback
        </Typography>
      </Toolbar>
      <Divider />
      <List dense sx={{ flex: 1 }}>
        {items.map((item) => (
          <ListItemButton
            key={item.to}
            component={Link}
            to={item.to}
            selected={loc.pathname === item.to || loc.pathname.startsWith(item.to + '/')}
            onClick={() => isSm && setOpen(false)}
          >
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
      <Divider />
      <Box sx={{ p: 2 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
          {user?.first_name} {user?.last_name}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
          {user?.role.name}
        </Typography>
        <ListItemButton onClick={() => logout().then(() => navigate('/login'))}>Abmelden</ListItemButton>
      </Box>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'grey.100' }}>
      <AppBar position="fixed" color="default" elevation={1} sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          {isSm && (
            <IconButton edge="start" onClick={() => setOpen(true)} sx={{ mr: 1 }}>
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            CAM Feedback & Post Learning
          </Typography>
        </Toolbar>
      </AppBar>
      <Box component="nav" sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}>
        <Drawer
          variant={isSm ? 'temporary' : 'permanent'}
          open={isSm ? open : true}
          onClose={() => setOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              boxSizing: 'border-box',
            },
          }}
        >
          {drawer}
        </Drawer>
      </Box>
      <Box component="main" sx={{ flexGrow: 1, p: 3, width: { md: `calc(100% - ${drawerWidth}px)` }, mt: 8 }}>
        {children}
      </Box>
    </Box>
  )
}
