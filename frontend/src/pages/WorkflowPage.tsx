import { Box, Paper, Stack, Typography } from '@mui/material'
import Grid from '@mui/material/Grid'

const steps = [
  {
    title: '1. Feedback',
    body: 'Shopfloor erfasst Störung mit Maschine, Post-Version und NC-Kontext. Programme als Anhang hochladen.',
  },
  {
    title: '2. Analyse',
    body: 'Engineering prüft den Fall, dokumentiert Root Cause und priorisiert. Status z. B. „In review“ → „Technically analyzed“.',
  },
  {
    title: '3. Umsetzung & Test',
    body: 'Change Requests verknüpfen, Programmierfälle definieren und mit dem Standardfall verknüpfen. Regression auf der Maschine mit Post-Version dokumentieren.',
  },
  {
    title: '4. Validierung & Abschluss',
    body: 'Retest Shopfloor oder Freigabe. Status bis „Approved“ / „Closed“. Wissen in der Datenbank festhalten.',
  },
]

export function WorkflowPage() {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Validierungskreislauf
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Klare Reihenfolge von Meldung bis Abschluss — in jedem Arbeitsschritt Anlegen, Bearbeiten und Löschen über die jeweiligen Menüs.
      </Typography>
      <Grid container spacing={2}>
        {steps.map((s) => (
          <Grid key={s.title} size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Stack spacing={1}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  {s.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {s.body}
                </Typography>
              </Stack>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
