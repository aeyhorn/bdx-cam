import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'
import './index.css'
import App from './App.tsx'
import { AuthProvider } from './context/AuthContext'

const qc = new QueryClient()

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#37474f' },
    secondary: { main: '#546e7a' },
    background: { default: '#eceff1', paper: '#ffffff' },
  },
  typography: {
    fontFamily: ['Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'].join(','),
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={qc}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>
)
