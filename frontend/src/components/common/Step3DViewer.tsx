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
    async function extractErrorMessage(e: unknown): Promise<string> {
      const err = e as {
        response?: { status?: number; data?: Blob | { detail?: string } | string }
        message?: string
      }
      const data = err.response?.data
      if (typeof data === 'string' && data.trim()) return data
      if (data && typeof data === 'object' && 'detail' in data && typeof data.detail === 'string') return data.detail
      if (data instanceof Blob) {
        try {
          const raw = await data.text()
          if (raw) {
            try {
              const parsed = JSON.parse(raw) as { detail?: string }
              if (parsed.detail) return parsed.detail
            } catch {
              if (raw.trim()) return raw.trim()
            }
          }
        } catch {
          // ignore parsing errors and fall back below
        }
      }
      if (err.response?.status) return `3D-Modell konnte nicht geladen werden (HTTP ${err.response.status}).`
      return err.message || '3D-Modell konnte nicht geladen werden.'
    }

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
        const detail = await extractErrorMessage(e)
        setError(detail)
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
