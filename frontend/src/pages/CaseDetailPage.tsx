import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Divider,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  MenuItem,
  Paper,
  Stack,
  Step,
  StepLabel,
  Stepper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material'
import Grid from '@mui/material/Grid'
import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import { invalidateCaseEcosystem } from '../lib/queryCache'
import { useAuth } from '../context/AuthContext'
import { TextFileEditorDialog } from '../components/common/TextFileEditorDialog'
import { Step3DViewer } from '../components/common/Step3DViewer'

type CaseDetail = {
  id: number
  ticket_no: string
  title: string
  description: string | null
  nc_program_name: string
  project_name?: string | null
  expected_behavior: string | null
  actual_behavior: string | null
  status?: { id: number; key: string; name: string }
  severity?: { id: number; name: string }
  priority?: { id: number; name: string }
  machine?: { id: number; name: string }
  control_system?: { id: number; name: string }
  post_processor_version?: { name: string; version: string }
  cam_step_model?: { id: number; code: string; name: string }
  generated_nc_attachment?: { id: number; file_name: string } | null
  reporter?: { first_name: string; last_name: string }
  assignee?: { first_name: string; last_name: string } | null
  status_id: number
  priority_id: number
  severity_id: number
  assignee_id: number | null
  machine_id: number
  post_processor_version_id: number
  control_system_id: number | null
  cam_step_model_id: number
  generated_nc_attachment_id: number | null
}

type Comment = {
  id: number
  text: string
  comment_type: string
  created_at: string
  author?: { first_name: string; last_name: string }
}

type Attachment = {
  id: number
  file_name: string
  file_type?: string | null
  attachment_role?: 'other' | 'post' | 'generated_program'
  linked_project_name?: string | null
  notes?: string | null
  created_at: string
  download_url?: string
}

type AgentRun = {
  id: number
  status: string
  trigger_mode: string
  output_summary?: string | null
  knowledge_entry_id?: number | null
  created_at: string
}

function statusKeyToStep(key: string): number {
  const early = new Set(['NEW', 'IN_REVIEW', 'FEEDBACK_REQUESTED'])
  const analyze = new Set(['TECHNICALLY_ANALYZED'])
  const implement = new Set(['CHANGE_REQUESTED', 'IN_IMPLEMENTATION', 'IN_TEST'])
  if (early.has(key)) return 0
  if (analyze.has(key)) return 1
  if (implement.has(key)) return 2
  return 3
}

export function CaseDetailPage() {
  const { id } = useParams()
  const qc = useQueryClient()
  const { user } = useAuth()
  const [tab, setTab] = useState(0)
  const caseId = Number(id)
  const isEng = user?.role.key === 'ENGINEERING' || user?.role.key === 'ADMIN'
  const isProd = user?.role.key === 'FEEDBACK_PRODUCTION'

  const [msg, setMsg] = useState<string | null>(null)

  const detail = useQuery({
    queryKey: ['case', caseId],
    enabled: Number.isFinite(caseId),
    queryFn: async () => (await api.get<CaseDetail>(`/api/v1/cases/${caseId}`)).data,
  })

  const statuses = useQuery({
    queryKey: ['statuses'],
    queryFn: async () => (await api.get<{ id: number; name: string }[]>('/api/v1/statuses')).data,
    enabled: isEng && tab === 0,
  })
  const priorities = useQuery({
    queryKey: ['priorities'],
    queryFn: async () => (await api.get<{ id: number; name: string }[]>('/api/v1/priorities')).data,
    enabled: isEng && tab === 0,
  })
  const severities = useQuery({
    queryKey: ['severities'],
    queryFn: async () => (await api.get<{ id: number; name: string }[]>('/api/v1/severities')).data,
    enabled: (isEng || isProd) && tab === 0,
  })
  const assignees = useQuery({
    queryKey: ['assignees'],
    queryFn: async () => (await api.get<{ id: number; first_name: string; last_name: string }[]>('/api/v1/users/assignees')).data,
    enabled: isEng && tab === 0,
  })

  const comments = useQuery({
    queryKey: ['case', caseId, 'comments'],
    enabled: tab === 1 && Number.isFinite(caseId),
    queryFn: async () => (await api.get<Comment[]>(`/api/v1/cases/${caseId}/comments`)).data,
  })

  const attachments = useQuery({
    queryKey: ['case', caseId, 'attachments'],
    enabled: Number.isFinite(caseId) && (tab === 2 || tab === 6 || (isEng && tab === 0)),
    queryFn: async () => (await api.get<Attachment[]>(`/api/v1/cases/${caseId}/attachments`)).data,
  })

  const rootCause = useQuery({
    queryKey: ['case', caseId, 'rc'],
    enabled: tab === 3 && Number.isFinite(caseId),
    queryFn: async () => (await api.get(`/api/v1/cases/${caseId}/root-cause`)).data as Record<string, unknown> | null,
  })

  const categories = useQuery({
    queryKey: ['categories'],
    queryFn: async () => (await api.get<{ id: number; name: string }[]>('/api/v1/categories')).data,
    enabled: isEng && tab === 3,
  })

  const history = useQuery({
    queryKey: ['case', caseId, 'hist'],
    enabled: tab === 4 && Number.isFinite(caseId),
    queryFn: async () => (await api.get(`/api/v1/cases/${caseId}/history`)).data as Record<string, unknown>[],
  })

  const agentRuns = useQuery({
    queryKey: ['case', caseId, 'agent-runs'],
    enabled: Number.isFinite(caseId) && tab === 5,
    queryFn: async () => (await api.get<AgentRun[]>(`/api/v1/agent-runs/case/${caseId}`)).data,
  })

  const startAgent = useMutation({
    mutationFn: async () => api.post('/api/v1/agent-runs/start', { case_id: caseId, trigger_mode: 'manual' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['case', caseId, 'agent-runs'] })
      qc.invalidateQueries({ queryKey: ['knowledge'] })
      setMsg('Agentenprüfung gestartet und abgeschlossen.')
    },
    onError: (e: unknown) => setMsg(String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? e)),
  })

  const relations = useQuery({
    queryKey: ['case', caseId, 'rel'],
    enabled: Number.isFinite(caseId) && isEng,
    queryFn: async () =>
      (await api.get<{ change_requests: { id: number; change_no: string; title: string }[]; test_cases: { id: number; title: string }[] }>(`/api/v1/cases/${caseId}/relations`)).data,
  })

  const crs = useQuery({
    queryKey: ['change-requests'],
    queryFn: async () => (await api.get<{ id: number; change_no: string; title: string }[]>('/api/v1/change-requests')).data,
    enabled: isEng && tab === 0,
  })
  const tcs = useQuery({
    queryKey: ['test-cases'],
    queryFn: async () => (await api.get<{ id: number; title: string }[]>('/api/v1/test-cases')).data,
    enabled: isEng && tab === 0,
  })
  const camSteps = useQuery({
    queryKey: ['cam-step-models'],
    queryFn: async () => (await api.get<{ id: number; code: string; name: string }[]>('/api/v1/cam-step-models')).data,
    enabled: isEng && tab === 0,
  })

  const [st, setSt] = useState('')
  const [pr, setPr] = useState('')
  const [se, setSe] = useState('')
  const [as, setAs] = useState('')
  const [camStep, setCamStep] = useState('')
  const [genNc, setGenNc] = useState('')

  useEffect(() => {
    const cd = detail.data
    if (!cd) return
    setSt(String(cd.status_id))
    setPr(String(cd.priority_id))
    setSe(String(cd.severity_id))
    setAs(cd.assignee_id != null ? String(cd.assignee_id) : '')
    setCamStep(String(cd.cam_step_model_id))
    setGenNc(cd.generated_nc_attachment_id != null ? String(cd.generated_nc_attachment_id) : '')
    setUploadProjectName((cd as { project_name?: string | null }).project_name ?? '')
  }, [detail.data])

  const patchCase = useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      await api.patch(`/api/v1/cases/${caseId}`, body)
    },
    onSuccess: () => {
      invalidateCaseEcosystem(qc, caseId)
      setMsg('Gespeichert.')
    },
    onError: (e: unknown) => setMsg(String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? e)),
  })

  const postComment = useMutation({
    mutationFn: async (payload: { text: string; comment_type: string }) =>
      api.post(`/api/v1/cases/${caseId}/comments`, payload),
    onSuccess: () => {
      invalidateCaseEcosystem(qc, caseId)
      setCText('')
      setMsg(null)
    },
  })

  const [cText, setCText] = useState('')
  const [cType, setCType] = useState('GENERAL')

  const [linkCr, setLinkCr] = useState('')
  const [linkTc, setLinkTc] = useState('')

  const linkCrMut = useMutation({
    mutationFn: async () => api.post(`/api/v1/change-requests/${linkCr}/link-case/${caseId}`),
    onSuccess: () => {
      invalidateCaseEcosystem(qc, caseId)
      setLinkCr('')
      setMsg('Change Request verknüpft.')
    },
    onError: (e: unknown) => setMsg(String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? e)),
  })

  const unlinkCrMut = useMutation({
    mutationFn: async (crId: number) => api.delete(`/api/v1/change-requests/${crId}/link-case/${caseId}`),
    onSuccess: () => invalidateCaseEcosystem(qc, caseId),
  })

  const linkTcMut = useMutation({
    mutationFn: async () => api.post(`/api/v1/cases/${caseId}/link-test-case/${linkTc}`),
    onSuccess: () => {
      invalidateCaseEcosystem(qc, caseId)
      setLinkTc('')
      setMsg('Testfall verknüpft.')
    },
    onError: (e: unknown) => setMsg(String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? e)),
  })

  const unlinkTcMut = useMutation({
    mutationFn: async (tcId: number) => api.delete(`/api/v1/cases/${caseId}/link-test-case/${tcId}`),
    onSuccess: () => invalidateCaseEcosystem(qc, caseId),
  })

  const delAtt = useMutation({
    mutationFn: async (aid: number) => api.delete(`/api/v1/attachments/${aid}`),
    onSuccess: () => invalidateCaseEcosystem(qc, caseId),
  })

  const patchAtt = useMutation({
    mutationFn: async (payload: { id: number; body: Record<string, unknown> }) =>
      api.patch(`/api/v1/attachments/${payload.id}`, payload.body),
    onSuccess: () => {
      invalidateCaseEcosystem(qc, caseId)
      setMsg('Dateiverknüpfung gespeichert.')
    },
    onError: (e: unknown) => setMsg(String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? e)),
  })

  const saveTextMut = useMutation({
    mutationFn: async (payload: { id: number; content: string }) =>
      api.patch(`/api/v1/attachments/${payload.id}/text`, { content: payload.content }),
    onSuccess: () => {
      setMsg('Textdatei gespeichert.')
      invalidateCaseEcosystem(qc, caseId)
    },
    onError: (e: unknown) => setMsg(String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? e)),
  })

  const step = useMemo(() => {
    const k = detail.data?.status?.key ?? 'NEW'
    return statusKeyToStep(k)
  }, [detail.data?.status?.key])

  async function downloadAtt(attId: number, name: string) {
    const res = await api.get(`/api/v1/attachments/${attId}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = name
    a.click()
    URL.revokeObjectURL(url)
  }

  function roleLabel(role: Attachment['attachment_role']): string {
    if (role === 'post') return 'Post-Datei'
    if (role === 'generated_program') return 'Generiertes Programm'
    return 'Sonstiges'
  }

  const [rcCat, setRcCat] = useState('')
  const [rcHyp, setRcHyp] = useState('')
  const [rcConf, setRcConf] = useState(false)
  const [rcCps, setRcCps] = useState('')
  const [rcNc, setRcNc] = useState('')

  useEffect(() => {
    const rc = rootCause.data
    if (!rc) {
      setRcCat('')
      setRcHyp('')
      setRcConf(false)
      setRcCps('')
      setRcNc('')
      return
    }
    setRcCat(rc.error_category_id != null ? String(rc.error_category_id as number) : '')
    setRcHyp((rc.hypothesis as string) ?? '')
    setRcConf(Boolean(rc.confirmed))
    setRcCps((rc.cps_reference as string) ?? '')
    setRcNc((rc.nc_pattern as string) ?? '')
  }, [rootCause.data])

  const saveRc = useMutation({
    mutationFn: async () => {
      const body = {
        error_category_id: rcCat ? Number(rcCat) : null,
        hypothesis: rcHyp || null,
        confirmed: rcConf,
        cps_reference: rcCps || null,
        nc_pattern: rcNc || null,
      }
      if (rootCause.data?.id) {
        await api.patch(`/api/v1/root-causes/${rootCause.data.id as number}`, body)
      } else {
        await api.post(`/api/v1/cases/${caseId}/root-cause`, body)
      }
    },
    onSuccess: () => {
      invalidateCaseEcosystem(qc, caseId)
      setMsg('Analyse gespeichert.')
    },
    onError: (e: unknown) => setMsg(String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? e)),
  })

  const [uploadRole, setUploadRole] = useState<'other' | 'post' | 'generated_program'>('other')
  const [uploadLinkProject, setUploadLinkProject] = useState(true)
  const [uploadProjectName, setUploadProjectName] = useState('')
  const [uploadNotes, setUploadNotes] = useState('')
  const [selectedStepAttachmentId, setSelectedStepAttachmentId] = useState('')
  const [metaOpen, setMetaOpen] = useState(false)
  const [metaAtt, setMetaAtt] = useState<Attachment | null>(null)
  const [metaRole, setMetaRole] = useState<'other' | 'post' | 'generated_program'>('other')
  const [metaProject, setMetaProject] = useState('')
  const [metaNotes, setMetaNotes] = useState('')
  const [textOpen, setTextOpen] = useState(false)
  const [textAttId, setTextAttId] = useState<number | null>(null)
  const [textFileName, setTextFileName] = useState('')
  const [textContent, setTextContent] = useState('')
  const [textLoading, setTextLoading] = useState(false)

  async function openTextEditor(att: Attachment) {
    try {
      setTextLoading(true)
      const { data } = await api.get<{ attachment_id: number; file_name: string; content: string }>(`/api/v1/attachments/${att.id}/text`)
      setTextAttId(data.attachment_id)
      setTextFileName(data.file_name)
      setTextContent(data.content)
      setTextOpen(true)
    } catch (e: unknown) {
      setMsg(String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? e))
    } finally {
      setTextLoading(false)
    }
  }

  function openMetaEditor(att: Attachment) {
    setMetaAtt(att)
    setMetaRole(att.attachment_role ?? 'other')
    setMetaProject(att.linked_project_name ?? '')
    setMetaNotes(att.notes ?? '')
    setMetaOpen(true)
  }

  if (!Number.isFinite(caseId)) return <Typography>Ungültige ID</Typography>
  if (detail.isLoading) return <Typography>Laden…</Typography>
  if (detail.error) return <Typography>Fehler beim Laden</Typography>

  const c = detail.data!

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {c.ticket_no} — {c.title}
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Maschine: {c.machine?.name}
        {c.control_system ? ` · Steuerung: ${c.control_system.name}` : ''} · Post: {c.post_processor_version?.name}{' '}
        {c.post_processor_version?.version}
        {c.cam_step_model ? ` · Step/CAM: ${c.cam_step_model.code} (${c.cam_step_model.name})` : ''}
        {c.generated_nc_attachment ? ` · NC-Datei: ${c.generated_nc_attachment.file_name}` : ''} · Status: {c.status?.name}
      </Typography>

      <Stepper activeStep={step} sx={{ my: 3 }}>
        <Step>
          <StepLabel>Feedback</StepLabel>
        </Step>
        <Step>
          <StepLabel>Analyse</StepLabel>
        </Step>
        <Step>
          <StepLabel>Change &amp; Test</StepLabel>
        </Step>
        <Step>
          <StepLabel>Validierung</StepLabel>
        </Step>
      </Stepper>

      {msg && (
        <Alert severity="info" sx={{ mb: 2 }} onClose={() => setMsg(null)}>
          {msg}
        </Alert>
      )}

      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        variant="scrollable"
        scrollButtons="auto"
        allowScrollButtonsMobile
        sx={{ mb: 2 }}
      >
        <Tab label="Übersicht" />
        <Tab label="Kommentare" />
        <Tab label="Anhänge (NC / Daten)" />
        <Tab label="Technische Analyse" />
        <Tab label="Historie" />
        <Tab label="Agentenprüfung" />
        <Tab label="3D Viewer" />
      </Tabs>

      {tab === 0 && (
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                NC &amp; Verhalten
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Programmname:</strong> {c.nc_program_name}
              </Typography>
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle2">Erwartet</Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>
                {c.expected_behavior || '—'}
              </Typography>
              <Typography variant="subtitle2">Ist-Verhalten</Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {c.actual_behavior || '—'}
              </Typography>
            </Paper>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Maschine &amp; Validierung
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Programme unter „Anhänge“ hochladen, auf der Maschine testen und Status / Regression entsprechend setzen.
              </Typography>
              {isEng && (
                <Stack spacing={2}>
                  <Typography variant="subtitle2">Fertigungszuordnung</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Step-/CAM-Modell und optional der konkrete generierte NC-Code (Anhang dieses Falls). Änderungen nur mit passender
                    Admin-Freigabe (Maschine · Steuerung · Post).
                  </Typography>
                  <TextField select label="Step- / CAM-Modell" fullWidth value={camStep} onChange={(e) => setCamStep(e.target.value)}>
                    {(camSteps.data ?? []).map((s) => (
                      <MenuItem key={s.id} value={s.id}>
                        {s.code} — {s.name}
                      </MenuItem>
                    ))}
                  </TextField>
                  <TextField select label="Generierter NC-Anhang" fullWidth value={genNc} onChange={(e) => setGenNc(e.target.value)}>
                    <MenuItem value="">
                      <em>— keine Auswahl —</em>
                    </MenuItem>
                    {(attachments.data ?? []).filter((a) => a.attachment_role === 'generated_program').map((a) => (
                      <MenuItem key={a.id} value={a.id}>
                        {a.file_name}
                      </MenuItem>
                    ))}
                  </TextField>
                  <Button
                    variant="outlined"
                    disabled={!camStep || patchCase.isPending}
                    onClick={() =>
                      patchCase.mutate({
                        cam_step_model_id: Number(camStep),
                        generated_nc_attachment_id: genNc === '' ? null : Number(genNc),
                      })
                    }
                  >
                    Zuordnung speichern
                  </Button>
                  <Divider />
                  <TextField
                    select
                    label="Status"
                    fullWidth
                    value={st}
                    onChange={(e) => setSt(e.target.value)}
                  >
                    {(statuses.data ?? []).map((s) => (
                      <MenuItem key={s.id} value={s.id}>
                        {s.name}
                      </MenuItem>
                    ))}
                  </TextField>
                  <TextField
                    select
                    label="Priorität"
                    fullWidth
                    value={pr}
                    onChange={(e) => setPr(e.target.value)}
                  >
                    {(priorities.data ?? []).map((s) => (
                      <MenuItem key={s.id} value={s.id}>
                        {s.name}
                      </MenuItem>
                    ))}
                  </TextField>
                  <TextField
                    select
                    label="Severity"
                    fullWidth
                    value={se}
                    onChange={(e) => setSe(e.target.value)}
                  >
                    {(severities.data ?? []).map((s) => (
                      <MenuItem key={s.id} value={s.id}>
                        {s.name}
                      </MenuItem>
                    ))}
                  </TextField>
                  <TextField
                    select
                    label="Bearbeiter (Assignee)"
                    fullWidth
                    value={as}
                    onChange={(e) => setAs(e.target.value)}
                  >
                    <MenuItem value="">
                      <em>— nicht zugewiesen —</em>
                    </MenuItem>
                    {(assignees.data ?? []).map((s) => (
                      <MenuItem key={s.id} value={s.id}>
                        {s.first_name} {s.last_name}
                      </MenuItem>
                    ))}
                  </TextField>
                  <Button
                    variant="contained"
                    onClick={() => {
                      patchCase.mutate({
                        status_id: Number(st),
                        priority_id: Number(pr),
                        severity_id: Number(se),
                        assignee_id: as === '' ? null : Number(as),
                      })
                    }}
                  >
                    Steuerung speichern
                  </Button>
                </Stack>
              )}
            </Paper>
          </Grid>
          {isEng && relations.data && (
            <Grid size={{ xs: 12 }}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Verknüpfungen (Change / Test)
                </Typography>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
                  <TextField select label="Change Request verknüpfen" size="small" sx={{ minWidth: 240 }} value={linkCr} onChange={(e) => setLinkCr(e.target.value)}>
                    {(crs.data ?? []).map((r) => (
                      <MenuItem key={r.id} value={r.id}>
                        {r.change_no} — {r.title}
                      </MenuItem>
                    ))}
                  </TextField>
                  <Button variant="outlined" disabled={!linkCr} onClick={() => linkCrMut.mutate()}>
                    Verknüpfen
                  </Button>
                  <TextField select label="Testfall verknüpfen" size="small" sx={{ minWidth: 240 }} value={linkTc} onChange={(e) => setLinkTc(e.target.value)}>
                    {(tcs.data ?? []).map((r) => (
                      <MenuItem key={r.id} value={r.id}>
                        {r.title}
                      </MenuItem>
                    ))}
                  </TextField>
                  <Button variant="outlined" disabled={!linkTc} onClick={() => linkTcMut.mutate()}>
                    Verknüpfen
                  </Button>
                </Stack>
                <Typography variant="caption" sx={{ display: 'block' }}>
                  Change Requests
                </Typography>
                <Stack spacing={0.5} sx={{ mb: 1 }}>
                  {(relations.data.change_requests ?? []).map((r) => (
                    <Stack key={r.id} direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                      <Typography variant="body2">
                        {r.change_no} — {r.title}
                      </Typography>
                      <Button size="small" color="error" onClick={() => unlinkCrMut.mutate(r.id)}>
                        Lösen
                      </Button>
                    </Stack>
                  ))}
                </Stack>
                <Typography variant="caption" sx={{ display: 'block' }}>
                  Testfälle
                </Typography>
                <Stack spacing={0.5}>
                  {(relations.data.test_cases ?? []).map((r) => (
                    <Stack key={r.id} direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                      <Typography variant="body2">{r.title}</Typography>
                      <Button size="small" color="error" onClick={() => unlinkTcMut.mutate(r.id)}>
                        Lösen
                      </Button>
                    </Stack>
                  ))}
                </Stack>
              </Paper>
            </Grid>
          )}
        </Grid>
      )}

      {tab === 1 && (
        <Box>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
            <TextField label="Kommentar" fullWidth multiline minRows={2} value={cText} onChange={(e) => setCText(e.target.value)} />
            <TextField select label="Typ" sx={{ minWidth: 160 }} value={cType} onChange={(e) => setCType(e.target.value)}>
              <MenuItem value="GENERAL">Allgemein</MenuItem>
              <MenuItem value="QUESTION">Frage</MenuItem>
              <MenuItem value="ANSWER">Antwort</MenuItem>
              {isEng && <MenuItem value="INTERNAL">Intern</MenuItem>}
            </TextField>
            <Button variant="contained" disabled={!cText} onClick={() => postComment.mutate({ text: cText, comment_type: cType })}>
              Senden
            </Button>
          </Stack>
          <Stack spacing={1}>
            {(comments.data ?? []).map((cm) => (
              <Paper key={cm.id} variant="outlined" sx={{ p: 1.5 }}>
                <Typography variant="caption" color="text.secondary">
                  {cm.author ? `${cm.author.first_name} ${cm.author.last_name}` : '—'} · {cm.comment_type} ·{' '}
                  {new Date(cm.created_at).toLocaleString()}
                </Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mt: 0.5 }}>
                  {cm.text}
                </Typography>
              </Paper>
            ))}
          </Stack>
        </Box>
      )}

      {tab === 2 && (
        <Box>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2, alignItems: { md: 'center' } }}>
            <TextField
              select
              label="Dateityp"
              size="small"
              value={uploadRole}
              onChange={(e) => setUploadRole(e.target.value as 'other' | 'post' | 'generated_program')}
              sx={{ minWidth: 220 }}
            >
              <MenuItem value="other">Sonstige Datei</MenuItem>
              <MenuItem value="post">Post-Datei</MenuItem>
              <MenuItem value="generated_program">Generiertes Programm</MenuItem>
            </TextField>
            <FormControlLabel
              control={<Checkbox checked={uploadLinkProject} onChange={(_, c) => setUploadLinkProject(c)} />}
              label="Mit Projekt verknüpfen"
            />
            <TextField
              label="Projektname"
              size="small"
              value={uploadProjectName}
              onChange={(e) => setUploadProjectName(e.target.value)}
              sx={{ minWidth: 240 }}
              disabled={!uploadLinkProject}
            />
            <TextField
              label="Notiz (optional)"
              size="small"
              value={uploadNotes}
              onChange={(e) => setUploadNotes(e.target.value)}
              sx={{ minWidth: 240 }}
            />
            <Button variant="outlined" component="label">
              Datei hochladen
              <input
                hidden
                type="file"
                onChange={async (e) => {
                  const f = e.target.files?.[0]
                  if (!f) return
                  const fd = new FormData()
                  fd.append('file', f)
                  fd.append('attachment_role', uploadRole)
                  fd.append('link_to_project', String(uploadLinkProject))
                  if (uploadProjectName) fd.append('linked_project_name', uploadProjectName)
                  if (uploadNotes) fd.append('notes', uploadNotes)
                  await api.post(`/api/v1/cases/${caseId}/attachments`, fd)
                  invalidateCaseEcosystem(qc, caseId)
                  e.target.value = ''
                  setUploadNotes('')
                }}
              />
            </Button>
          </Stack>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Datei</TableCell>
                <TableCell>Typ</TableCell>
                <TableCell>Projekt</TableCell>
                <TableCell>Zeit</TableCell>
                <TableCell align="right">Aktionen</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(attachments.data ?? []).map((a) => (
                <TableRow key={a.id}>
                  <TableCell>{a.file_name}</TableCell>
                  <TableCell>{roleLabel(a.attachment_role)}</TableCell>
                  <TableCell>{a.linked_project_name || '—'}</TableCell>
                  <TableCell>{new Date(a.created_at).toLocaleString()}</TableCell>
                  <TableCell align="right">
                    <Button size="small" onClick={() => openMetaEditor(a)}>
                      Zuordnung
                    </Button>
                    <Button size="small" disabled={textLoading} onClick={() => void openTextEditor(a)}>
                      Editor
                    </Button>
                    <Button size="small" onClick={() => downloadAtt(a.id, a.file_name)}>
                      Download
                    </Button>
                    <Button size="small" color="error" onClick={() => delAtt.mutate(a.id)}>
                      Löschen
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>
      )}

      {tab === 3 && isEng && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Root Cause
          </Typography>
          <Stack spacing={2} sx={{ maxWidth: 560 }}>
            <TextField select label="Fehlerkategorie" fullWidth value={rcCat} onChange={(e) => setRcCat(e.target.value)}>
              <MenuItem value="">
                <em>—</em>
              </MenuItem>
              {(categories.data ?? []).map((cat) => (
                <MenuItem key={cat.id} value={cat.id}>
                  {cat.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField label="Hypothese" fullWidth multiline minRows={2} value={rcHyp} onChange={(e) => setRcHyp(e.target.value)} />
            <TextField label="CPS-Referenz" fullWidth value={rcCps} onChange={(e) => setRcCps(e.target.value)} />
            <TextField label="NC-Muster" fullWidth multiline minRows={2} value={rcNc} onChange={(e) => setRcNc(e.target.value)} />
            <TextField select label="Bestätigt" value={String(rcConf)} onChange={(e) => setRcConf(e.target.value === 'true')}>
              <MenuItem value="false">Nein</MenuItem>
              <MenuItem value="true">Ja</MenuItem>
            </TextField>
            <Button variant="contained" onClick={() => saveRc.mutate()}>
              Speichern
            </Button>
          </Stack>
        </Paper>
      )}

      {tab === 3 && !isEng && (
        <Typography variant="body2" color="text.secondary">
          Technische Analyse ist für Engineering / Admin sichtbar.
        </Typography>
      )}

      {tab === 4 && (
        <Stack spacing={1}>
          {(history.data ?? []).map((h, i) => (
            <Paper key={i} variant="outlined" sx={{ p: 1 }}>
              <Typography variant="caption" component="pre" sx={{ fontSize: 11, whiteSpace: 'pre-wrap', m: 0 }}>
                {JSON.stringify(h, null, 2)}
              </Typography>
            </Paper>
          ))}
        </Stack>
      )}

      {tab === 5 && (
        <Stack spacing={2}>
          <Button variant="contained" onClick={() => startAgent.mutate()} disabled={startAgent.isPending}>
            Agentenprüfung starten
          </Button>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Trigger</TableCell>
                <TableCell>Zusammenfassung</TableCell>
                <TableCell>Knowledge-ID</TableCell>
                <TableCell>Zeit</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(agentRuns.data ?? []).map((r) => (
                <TableRow key={r.id}>
                  <TableCell>{r.id}</TableCell>
                  <TableCell>{r.status}</TableCell>
                  <TableCell>{r.trigger_mode}</TableCell>
                  <TableCell>{r.output_summary || '—'}</TableCell>
                  <TableCell>{r.knowledge_entry_id ?? '—'}</TableCell>
                  <TableCell>{new Date(r.created_at).toLocaleString()}</TableCell>
                </TableRow>
              ))}
              {(agentRuns.data ?? []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={6}>Noch keine Agentenläufe vorhanden.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Stack>
      )}

      {tab === 6 && (
        <Stack spacing={2}>
          <TextField
            select
            label="STEP-Datei"
            size="small"
            sx={{ maxWidth: 420 }}
            value={selectedStepAttachmentId}
            onChange={(e) => setSelectedStepAttachmentId(e.target.value)}
          >
            <MenuItem value="">
              <em>— bitte wählen —</em>
            </MenuItem>
            {(attachments.data ?? [])
              .filter((a) => {
                const name = a.file_name.toLowerCase()
                return name.endsWith('.step') || name.endsWith('.stp')
              })
              .map((a) => (
                <MenuItem key={a.id} value={a.id}>
                  {a.file_name}
                </MenuItem>
              ))}
          </TextField>
          <Step3DViewer
            attachment={
              selectedStepAttachmentId
                ? ((attachments.data ?? []).find((a) => a.id === Number(selectedStepAttachmentId)) ?? null)
                : null
            }
          />
        </Stack>
      )}

      <Dialog open={metaOpen} onClose={() => setMetaOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Datei-Zuordnung</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <TextField
              label="Datei"
              value={metaAtt?.file_name ?? ''}
              fullWidth
              slotProps={{ input: { readOnly: true } }}
            />
            <TextField select label="Typ" fullWidth value={metaRole} onChange={(e) => setMetaRole(e.target.value as 'other' | 'post' | 'generated_program')}>
              <MenuItem value="other">Sonstige Datei</MenuItem>
              <MenuItem value="post">Post-Datei</MenuItem>
              <MenuItem value="generated_program">Generiertes Programm</MenuItem>
            </TextField>
            <TextField label="Verknüpftes Projekt" fullWidth value={metaProject} onChange={(e) => setMetaProject(e.target.value)} />
            <TextField label="Notizen" fullWidth multiline minRows={2} value={metaNotes} onChange={(e) => setMetaNotes(e.target.value)} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMetaOpen(false)}>Abbrechen</Button>
          <Button
            variant="contained"
            disabled={!metaAtt || patchAtt.isPending}
            onClick={() => {
              if (!metaAtt) return
              patchAtt.mutate({
                id: metaAtt.id,
                body: {
                  attachment_role: metaRole,
                  linked_project_name: metaProject || null,
                  notes: metaNotes || null,
                },
              })
              setMetaOpen(false)
            }}
          >
            Speichern
          </Button>
        </DialogActions>
      </Dialog>

      <TextFileEditorDialog
        open={textOpen}
        title={`Text-Editor: ${textFileName}`}
        content={textContent}
        onChange={setTextContent}
        onClose={() => setTextOpen(false)}
        onSave={() => textAttId != null && saveTextMut.mutate({ id: textAttId, content: textContent })}
        isSaving={saveTextMut.isPending}
        saveDisabled={textAttId == null}
      />
    </Box>
  )
}
