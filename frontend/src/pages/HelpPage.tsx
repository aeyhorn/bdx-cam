import { Paper, Typography } from '@mui/material'

export function HelpPage() {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Hilfe
      </Typography>
      <Typography variant="body2">
        Erfassen Sie Feedback direkt aus der Fertigung: Maschine, Post-Version und NC-Programm sind Pflichtfelder. Engineering
        analysiert den Fall und kann Rückfragen stellen.
      </Typography>
    </Paper>
  )
}
