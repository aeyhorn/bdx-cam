import { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import { Alert, Box, Button, Container, Paper, TextField, Typography } from '@mui/material'
import { useAuth } from '../context/AuthContext'

function formatLoginError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    if (err.code === 'ERR_NETWORK' || err.message === 'Network Error') {
      return 'Server nicht erreichbar. Läuft das Backend (z. B. Docker „backend“) und ist es bereit?'
    }
    const detail = err.response?.data && typeof err.response.data === 'object' && 'detail' in err.response.data
      ? (err.response.data as { detail?: unknown }).detail
      : undefined
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail[0] && typeof detail[0] === 'object' && 'msg' in detail[0]) {
      return String((detail[0] as { msg: string }).msg)
    }
  }
  return 'Anmeldung fehlgeschlagen.'
}

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(formatLoginError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 10 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h5" gutterBottom>
          Anmeldung
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          BDXPostOffice
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <Box component="form" onSubmit={onSubmit}>
          <TextField
            label="E-Mail"
            type="email"
            fullWidth
            margin="normal"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <TextField
            label="Passwort"
            type="password"
            fullWidth
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }} disabled={loading}>
            {loading ? '…' : 'Anmelden'}
          </Button>
        </Box>
      </Paper>
    </Container>
  )
}
