import { Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField } from '@mui/material'

type TextFileEditorDialogProps = {
  open: boolean
  title: string
  content: string
  onChange: (value: string) => void
  onClose: () => void
  onSave: () => void
  isSaving?: boolean
  saveDisabled?: boolean
}

export function TextFileEditorDialog({
  open,
  title,
  content,
  onChange,
  onClose,
  onSave,
  isSaving = false,
  saveDisabled = false,
}: TextFileEditorDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <TextField
          fullWidth
          multiline
          minRows={18}
          value={content}
          onChange={(e) => onChange(e.target.value)}
          slotProps={{ input: { sx: { fontFamily: 'Consolas, monospace', fontSize: 12 } } }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Schließen</Button>
        <Button variant="contained" disabled={saveDisabled || isSaving} onClick={onSave}>
          Speichern
        </Button>
      </DialogActions>
    </Dialog>
  )
}

