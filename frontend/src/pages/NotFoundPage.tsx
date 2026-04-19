import { Typography } from '@mui/material'
import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <Typography>
      Seite nicht gefunden. <Link to="/dashboard">Zurück</Link>
    </Typography>
  )
}
