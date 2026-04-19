import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Button,
  Divider,
  Paper,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material'
import Grid from '@mui/material/Grid'
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

export function CaseDetailPage() {
  const { id } = useParams()
  const qc = useQueryClient()
  const { user } = useAuth()
  const [tab, setTab] = useState(0)
  const caseId = Number(id)

  const detail = useQuery({
    queryKey: ['case', caseId],
    enabled: Number.isFinite(caseId),
    queryFn: async () => (await api.get(`/api/v1/cases/${caseId}`)).data,
  })

  const comments = useQuery({
    queryKey: ['case', caseId, 'comments'],
    enabled: tab === 1 && Number.isFinite(caseId),
    queryFn: async () => (await api.get(`/api/v1/cases/${caseId}/comments`)).data,
  })

  const attachments = useQuery({
    queryKey: ['case', caseId, 'attachments'],
    enabled: tab === 2 && Number.isFinite(caseId),
    queryFn: async () => (await api.get(`/api/v1/cases/${caseId}/attachments`)).data,
  })

  const rootCause = useQuery({
    queryKey: ['case', caseId, 'rc'],
    enabled: tab === 3 && Number.isFinite(caseId),
    queryFn: async () => (await api.get(`/api/v1/cases/${caseId}/root-cause`)).data,
  })

  const history = useQuery({
    queryKey: ['case', caseId, 'hist'],
    enabled: tab === 4 && Number.isFinite(caseId),
    queryFn: async () => (await api.get(`/api/v1/cases/${caseId}/history`)).data,
  })

  const relations = useQuery({
    queryKey: ['case', caseId, 'rel'],
    enabled: Number.isFinite(caseId) && (user?.role.key === 'ENGINEERING' || user?.role.key === 'ADMIN'),
    queryFn: async () => (await api.get(`/api/v1/cases/${caseId}/relations`)).data,
  })

  const postComment = useMutation({
    mutationFn: async (payload: { text: string; comment_type: string }) =>
      api.post(`/api/v1/cases/${caseId}/comments`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['case', caseId, 'comments'] }),
  })

  const [cText, setCText] = useState('')
  const [cType, setCType] = useState('GENERAL')

  if (!Number.isFinite(caseId)) return <Typography>Ungültige ID</Typography>
  if (detail.isLoading) return <Typography>Laden…</Typography>
  if (detail.error) return <Typography>Fehler</Typography>

  const c = detail.data

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {c.ticket_no} — {c.title}
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Maschine: {c.machine?.name} · Post: {c.post_processor_version?.name} {c.post_processor_version?.version} · Status:{' '}
        {c.status?.name}
      </Typography>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Übersicht" />
        <Tab label="Kommentare" />
        <Tab label="Anhänge" />
        <Tab label="Technische Analyse" />
        <Tab label="Historie" />
      </Tabs>

      {tab === 0 && (
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2">NC-Programm</Typography>
              <Typography variant="body2">{c.nc_program_name}</Typography>
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle2">Erwartetes Verhalten</Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {c.expected_behavior || '—'}
              </Typography>
            </Paper>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2">Tatsächliches Verhalten</Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {c.actual_behavior || '—'}
              </Typography>
            </Paper>
          </Grid>
          {relations.data && (
            <Grid size={{ xs: 12 }}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle2">Verknüpfungen</Typography>
                <Typography variant="caption" sx={{ display: 'block' }}>
                  Change Requests: {relations.data.change_requests?.length ?? 0}
                </Typography>
                <Typography variant="caption" sx={{ display: 'block' }}>
                  Testfälle: {relations.data.test_cases?.length ?? 0}
                </Typography>
              </Paper>
            </Grid>
          )}
        </Grid>
      )}

      {tab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
            <TextField
              label="Kommentar"
              fullWidth
              multiline
              minRows={2}
              value={cText}
              onChange={(e) => setCText(e.target.value)}
            />
            <TextField
              label="Typ"
              select
              slotProps={{ select: { native: true } }}
              value={cType}
              onChange={(e) => setCType(e.target.value)}
            >
              <option value="GENERAL">Allgemein</option>
              <option value="QUESTION">Frage</option>
              <option value="ANSWER">Antwort</option>
              {(user?.role.key === 'ENGINEERING' || user?.role.key === 'ADMIN') && (
                <option value="INTERNAL">Intern</option>
              )}
            </TextField>
            <Button
              variant="contained"
              onClick={() => postComment.mutate({ text: cText, comment_type: cType })}
              disabled={!cText}
            >
              Senden
            </Button>
          </Box>
          <pre style={{ fontSize: 12 }}>{JSON.stringify(comments.data, null, 2)}</pre>
        </Box>
      )}

      {tab === 2 && (
        <Box>
          <Button variant="outlined" component="label" sx={{ mb: 1 }}>
            Datei wählen
            <input
              hidden
              type="file"
              onChange={async (e) => {
                const f = e.target.files?.[0]
                if (!f) return
                const fd = new FormData()
                fd.append('file', f)
                await api.post(`/api/v1/cases/${caseId}/attachments`, fd, {
                  headers: { 'Content-Type': 'multipart/form-data' },
                })
                attachments.refetch()
              }}
            />
          </Button>
          <pre style={{ fontSize: 12 }}>{JSON.stringify(attachments.data, null, 2)}</pre>
        </Box>
      )}

      {tab === 3 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Root Cause
          </Typography>
          <pre style={{ fontSize: 12 }}>{JSON.stringify(rootCause.data, null, 2)}</pre>
        </Paper>
      )}

      {tab === 4 && <pre style={{ fontSize: 12 }}>{JSON.stringify(history.data, null, 2)}</pre>}
    </Box>
  )
}
