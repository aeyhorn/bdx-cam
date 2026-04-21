import '@google/model-viewer'
import { Alert, Box, CircularProgress, Stack, Typography } from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'

type StepAttachment = {
  id: number
  file_name: string
}

type Props = {
  attachment: StepAttachment | null
}

export function Step3DViewer({ attachment }: Props) {
  const [modelUrl, setModelUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const endpoint = useMemo(
    () => (attachment ? `/api/v1/attachments/${attachment.id}/viewer-model` : null),
    [attachment],
  )

  useEffect(() => {
    let currentUrl: string | null = null
    async function load() {
      if (!endpoint) {
        setModelUrl(null)
        setError(null)
        return
      }
      try {
        setLoading(true)
        setError(null)
        const res = await api.get(endpoint, { responseType: 'blob' })
        currentUrl = URL.createObjectURL(res.data)
        setModelUrl(currentUrl)
      } catch (e: unknown) {
        const detail = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        setError(detail ?? '3D-Modell konnte nicht geladen werden.')
        setModelUrl(null)
      } finally {
        setLoading(false)
      }
    }
    void load()
    return () => {
      if (currentUrl) URL.revokeObjectURL(currentUrl)
    }
  }, [endpoint])

  if (!attachment) {
    return (
      <Alert severity="info">
        Keine STEP-Datei ausgewählt.
      </Alert>
    )
  }

  return (
    <Stack spacing={1}>
      <Typography variant="body2" color="text.secondary">
        Datei: {attachment.file_name}
      </Typography>
      {loading && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CircularProgress size={18} />
          <Typography variant="body2">Konvertiere und lade 3D-Modell…</Typography>
        </Box>
      )}
      {error && <Alert severity="error">{error}</Alert>}
      {modelUrl && (
        <Box sx={{ height: 520, borderRadius: 1, overflow: 'hidden', border: '1px solid', borderColor: 'divider', bgcolor: '#111' }}>
          <model-viewer
            src={modelUrl}
            camera-controls
            touch-action="pan-y"
            exposure="1"
            shadow-intensity="0.9"
            style={{ width: '100%', height: '100%' }}
          />
        </Box>
      )}
    </Stack>
  )
}
