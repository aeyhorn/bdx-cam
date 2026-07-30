import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../api/client'

type TestCaseRow = {
  id: number
  title: string
  description?: string | null
  machine?: { id: number; name: string } | null
  control_system?: { id: number; name: string } | null
  scenario_type?: string | null
  expected_result?: string | null
  risk_level?: string | null
}

type Attachment = {
  id: number
  file_name: string
  attachment_role: string
  linked_project_name?: string | null
}

type TestCaseDetail = TestCaseRow & {
  regression_count: number
  attachments: Attachment[]
}

type PostVersion = {
  id: number
  name: string
  version: string
  machine_family: string
}

const results = [
  { value: 'passed', label: 'Bestanden' },
  { value: 'failed', label: 'Fehlgeschlagen' },
  { value: 'partial', label: 'Teilweise' },
]

function extractErr(e: unknown): string {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const ax = e as any
  return String(ax?.response?.data?.detail ?? ax?.message ?? 'Anfrage fehlgeschlagen')
}

function classifyAttachment(fileName: string, role: string): string {
  const ext = fileName.split('.').pop()?.toLowerCase() ?? ''
  if (role === 'program') return 'Programm'
  if (role === 'step' || ext === 'step' || ext === 'stp') return 'STEP'
  if (ext === 'nc' || ext === 'tap' || ext === 'gcode') return 'NC'
  return 'Datei'
}

export function ShopfloorTestRunsPage() {
  const qc = useQueryClient()
  const [detailId, setDetailId] = useState<number | null>(null)
  const [postVersionId, setPostVersionId] = useState('')
  const [result, setResult] = useState('passed')
  const [notes, setNotes] = useState('')
  const [err, setErr] = useState<string | null>(null)
  const [textOpen, setTextOpen] = useState(false)
  const [textTitle, setTextTitle] = useState('')
  const [textContent, setTextContent] = useState('')
  const [publishMsg, setPublishMsg] = useState<string | null>(null)

  const list = useQuery({
    queryKey: ['shopfloor-test-cases'],
    queryFn: async () => (await api.get<TestCaseRow[]>('/api/v1/test-cases/shopfloor')).data,
  })
  const detail = useQuery({
    queryKey: ['shopfloor-test-case-detail', detailId],
    enabled: detailId != null,
    queryFn: async () => (await api.get<TestCaseDetail>(`/api/v1/test-cases/shopfloor/${detailId}/detail`)).data,
  })
  const postVersions = useQuery({
    queryKey: ['post-versions'],
    queryFn: async () => (await api.get<PostVersion[]>('/api/v1/post-versions')).data,
  })

  const reportMut = useMutation({
    mutationFn: async () => {
      if (!detailId) throw new Error('Kein Programmierfall gewaehlt')
      await api.post(`/api/v1/test-cases/shopfloor/${detailId}/result`, {
        post_processor_version_id: Number(postVersionId),
        result,
        notes: notes.trim() || null,
      })
    },
    onSuccess: async () => {
      setErr(null)
      setPostVersionId('')
      setResult('passed')
      setNotes('')
      await qc.invalidateQueries({ queryKey: ['shopfloor-test-case-detail', detailId] })
      await qc.invalidateQueries({ queryKey: ['regression-runs'] })
    },
    onError: (e: unknown) => setErr(extractErr(e)),
  })

  const publishMut = useMutation({
    mutationFn: async (att: Attachment) => {
      const { data } = await api.post<{ file_name: string; target_path: string; bytes: number }>(
        `/api/v1/test-case-attachments/${att.id}/publish-nc`
      )
      return data
    },
    onSuccess: (data) => {
      setErr(null)
      setPublishMsg(`${data.file_name} wurde an die Maschine uebertragen.`)
    },
    onError: (e: unknown) => {
      setPublishMsg(null)
      setErr(extractErr(e))
    },
  })

  async function downloadAttachment(id: number, fileName: string) {
    const resp = await api.get(`/api/v1/test-case-attachments/${id}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(resp.data)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  async function showAttachment(id: number, fileName: string) {
    try {
      const { data } = await api.get<{ file_name: string; content: string }>(`/api/v1/test-case-attachments/${id}/text`)
      setTextTitle(data.file_name)
      setTextContent(data.content)
      setTextOpen(true)
    } catch {
      await downloadAttachment(id, fileName)
    }
  }

  function canPublishAttachment(a: Attachment): boolean {
    const ext = a.file_name.split('.').pop()?.toLowerCase() ?? ''
    return a.attachment_role === 'program' || ['nc', 'tap', 'gcode', 'mpf', 'spf', 'h'].includes(ext)
  }

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Pruefauftraege
      </Typography>
      {(list.data?.length ?? 0) === 0 && !list.isLoading && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Es sind aktuell keine Programmierfaelle fuer Shopfloor freigegeben.
        </Alert>
      )}
      <Paper sx={{ p: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Titel</TableCell>
              <TableCell>Maschine</TableCell>
              <TableCell>Steuerung</TableCell>
              <TableCell>Szenario</TableCell>
              <TableCell align="right">Aktion</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(list.data ?? []).map((tc) => (
              <TableRow key={tc.id} hover>
                <TableCell>{tc.id}</TableCell>
                <TableCell>{tc.title}</TableCell>
                <TableCell>{tc.machine?.name ?? '-'}</TableCell>
                <TableCell>{tc.control_system?.name ?? '-'}</TableCell>
                <TableCell>{tc.scenario_type ?? '-'}</TableCell>
                <TableCell align="right">
                  <Button
                    size="small"
                    onClick={() => {
                      setDetailId(tc.id)
                      setErr(null)
                    }}
                  >
                    Pruefen
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {list.isLoading && (
              <TableRow>
                <TableCell colSpan={6}>Lade Pruefauftraege...</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={detailId != null} onClose={() => setDetailId(null)} maxWidth="lg" fullWidth>
        <DialogTitle>Programmierfall pruefen</DialogTitle>
        <DialogContent>
          {detail.isLoading && <Typography>Lade Programmierfall...</Typography>}
          {!detail.isLoading && detail.data && (
            <Stack spacing={2} sx={{ pt: 1 }}>
              {err && <Alert severity="error">{err}</Alert>}
              {publishMsg && <Alert severity="success">{publishMsg}</Alert>}
              {reportMut.isSuccess && <Alert severity="success">Rueckmeldung gespeichert.</Alert>}
              <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
                <Chip label={`ID ${detail.data.id}`} size="small" />
                <Chip label={detail.data.machine?.name ? `Maschine: ${detail.data.machine.name}` : 'Maschine: -'} size="small" />
                <Chip label={detail.data.control_system?.name ? `Steuerung: ${detail.data.control_system.name}` : 'Steuerung: -'} size="small" />
                <Chip label={`Rueckmeldungen: ${detail.data.regression_count}`} size="small" />
              </Stack>
              <Typography variant="h6">{detail.data.title}</Typography>
              <Typography variant="body2">{detail.data.description || 'Keine Beschreibung'}</Typography>
              <Typography variant="body2">
                <b>Erwartung:</b> {detail.data.expected_result || '-'}
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Datei</TableCell>
                    <TableCell>Klasse</TableCell>
                    <TableCell>Projekt</TableCell>
                    <TableCell align="right">Aktion</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {detail.data.attachments.map((a) => (
                    <TableRow key={a.id}>
                      <TableCell>{a.file_name}</TableCell>
                      <TableCell>{classifyAttachment(a.file_name, a.attachment_role)}</TableCell>
                      <TableCell>{a.linked_project_name || '-'}</TableCell>
                      <TableCell align="right">
                        <Button size="small" onClick={() => void showAttachment(a.id, a.file_name)}>
                          Anzeigen
                        </Button>
                        <Button size="small" onClick={() => void downloadAttachment(a.id, a.file_name)}>
                          Download
                        </Button>
                        {canPublishAttachment(a) && (
                          <Button size="small" disabled={publishMut.isPending} onClick={() => publishMut.mutate(a)}>
                            An Maschine
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {detail.data.attachments.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4}>Keine Dateien vorhanden.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
                <TextField select label="Post-Version auf Maschine" required size="small" value={postVersionId} onChange={(e) => setPostVersionId(e.target.value)} sx={{ minWidth: 240 }}>
                  <MenuItem value="">
                    <em>bitte waehlen</em>
                  </MenuItem>
                  {(postVersions.data ?? []).map((p) => (
                    <MenuItem key={p.id} value={p.id}>
                      {p.name} {p.version}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField select label="Ergebnis" size="small" value={result} onChange={(e) => setResult(e.target.value)} sx={{ minWidth: 180 }}>
                  {results.map((r) => (
                    <MenuItem key={r.value} value={r.value}>
                      {r.label}
                    </MenuItem>
                  ))}
                </TextField>
              </Stack>
              <TextField label="Rueckmeldung / Beobachtung" fullWidth multiline minRows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailId(null)}>Schliessen</Button>
          <Button variant="contained" disabled={!postVersionId || reportMut.isPending} onClick={() => reportMut.mutate()}>
            Ergebnis speichern
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={textOpen} onClose={() => setTextOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>{textTitle}</DialogTitle>
        <DialogContent>
          <Box component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: 12 }}>
            {textContent}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTextOpen(false)}>Schliessen</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
