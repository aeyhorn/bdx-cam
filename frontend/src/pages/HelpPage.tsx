import { Paper, Typography } from '@mui/material'

export function HelpPage() {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Hilfe
      </Typography>
      <Typography variant="body2" sx={{ mb: 2 }}>
        Unter <strong>Problem melden</strong> wählen Sie zuerst Ihre Maschine samt Programmumgebung (ein Eintrag), tragen den
        <strong> NC-Programmnamen</strong> ein und beschreiben in wenigen Sätzen das Problem. Titel und technische Zusatzfelder sind
        optional.
      </Typography>
      <Typography variant="body2" sx={{ mb: 2 }}>
        <strong>Standardfall</strong>: singuläre Betrachtung eines einzelnen Maschinen-/Prozessproblems.
        <br />
        <strong>Programmierfall</strong>: Fall aus der Teileprogrammierung (inkl. NC/STEP/Dateianhängen), der mit Standardfällen
        verknüpft werden kann.
      </Typography>
      <Typography variant="body2">
        Die Kombination <strong>Maschine · Steuerung · Postprozessor</strong> muss vom Administrator unter „Fertigungsbindungen“
        freigegeben sein. Optional kann Engineering später den konkreten generierten NC-Anhang am Standardfall verknüpfen.
      </Typography>
    </Paper>
  )
}
