import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Divider,
  MenuItem,
  Paper,
  TextField,
  Typography,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import Grid from '@mui/material/Grid'
import { useEffect, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { api } from '../api/client'
import { invalidateCaseEcosystem } from '../lib/queryCache'

type BindingRow = {
  id: number
  machine_id: number
  post_processor_version_id: number
  control_system_id: number
  machine?: { name: string }
  post_processor_version?: { name: string; version: string }
  control_system?: { name: string }
}

function bindingLabel(b: BindingRow): string {
  const m = b.machine?.name ?? `Maschine #${b.machine_id}`
  const cs = b.control_system?.name ?? `Steuerung #${b.control_system_id}`
  const pp = b.post_processor_version ? `${b.post_processor_version.name} ${b.post_processor_version.version}` : `Post #${b.post_processor_version_id}`
  return `${m} · ${cs} · ${pp}`
}

const quickSchema = z.object({
  binding_id: z.preprocess(
    (v) => (v === '' || v === undefined || v === null ? NaN : Number(v)),
    z.number().refine((n) => Number.isFinite(n) && n > 0, 'Bitte Maschine / Umgebung wählen')
  ),
  nc_program_name: z.string().min(1, 'NC-Programmname eingeben'),
  title: z.string().optional(),
  description: z.string().min(1, 'Bitte kurz beschreiben, was passiert ist'),
  severity_id: z.preprocess(
    (v) => (v === '' || v === undefined || v === null ? NaN : Number(v)),
    z.number().refine((n) => Number.isFinite(n) && n > 0, 'Bitte Dringlichkeit wählen')
  ),
  cam_step_model_id: z.preprocess(
    (v) => (v === '' || v === undefined || v === null ? undefined : Number(v)),
    z.number().optional()
  ),
  project_name: z.string().optional(),
  part_name: z.string().optional(),
  nc_line_reference: z.string().optional(),
  expected_behavior: z.string().optional(),
  actual_behavior: z.string().optional(),
})

export function NewFeedbackPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const sev = useQuery({
    queryKey: ['severities'],
    queryFn: async () => (await api.get<{ id: number; name: string }[]>('/api/v1/severities')).data,
  })
  const camSteps = useQuery({
    queryKey: ['cam-step-models'],
    queryFn: async () => (await api.get<{ id: number; code: string; name: string }[]>('/api/v1/cam-step-models')).data,
  })
  const bindings = useQuery({
    queryKey: ['machine-post-bindings'],
    queryFn: async () => (await api.get<BindingRow[]>('/api/v1/machine-post-bindings')).data,
  })

  const camDefaultApplied = useRef(false)
  const { register, handleSubmit, setValue, setError, clearErrors, formState } = useForm<Record<string, unknown>>({
    defaultValues: {
      binding_id: '',
      nc_program_name: '',
      title: '',
      description: '',
      severity_id: '',
      cam_step_model_id: '',
      project_name: '',
      part_name: '',
      nc_line_reference: '',
      expected_behavior: '',
      actual_behavior: '',
    },
  })

  useEffect(() => {
    if (camDefaultApplied.current || !camSteps.data?.length) return
    const legacy = camSteps.data.find((c) => c.code === 'LEGACY')
    if (legacy) {
      setValue('cam_step_model_id', String(legacy.id), { shouldDirty: false })
      camDefaultApplied.current = true
    }
  }, [camSteps.data, setValue])

  async function onSubmit(raw: Record<string, unknown>) {
    clearErrors()
    const parsed = quickSchema.safeParse(raw)
    if (!parsed.success) {
      const fe = parsed.error.flatten().fieldErrors
      if (fe.binding_id?.[0]) setError('binding_id', { message: fe.binding_id[0] })
      else if (fe.nc_program_name?.[0]) setError('nc_program_name', { message: fe.nc_program_name[0] })
      else if (fe.severity_id?.[0]) setError('severity_id', { message: fe.severity_id[0] })
      else if (fe.description?.[0]) setError('description', { message: fe.description[0] })
      else setError('nc_program_name', { message: 'Eingaben prüfen' })
      return
    }
    const v = parsed.data
    const b = bindings.data?.find((x) => x.id === v.binding_id)
    if (!b) {
      setError('binding_id', { message: 'Ungültige Auswahl — bitte erneut wählen.' })
      return
    }
    const legacy = camSteps.data?.find((c) => c.code === 'LEGACY')
    const camId =
      v.cam_step_model_id && v.cam_step_model_id > 0 ? v.cam_step_model_id : legacy?.id ?? camSteps.data?.[0]?.id
    if (!camId) {
      setError('nc_program_name', { message: 'Kein CAM-Standard verfügbar — bitte Administrator informieren.' })
      return
    }
    const title = (v.title?.trim() || v.nc_program_name.trim()).slice(0, 512)
    try {
      const { data } = await api.post<{ id: number }>('/api/v1/cases', {
        title,
        description: v.description.trim() || null,
        machine_id: b.machine_id,
        post_processor_version_id: b.post_processor_version_id,
        control_system_id: b.control_system_id,
        cam_step_model_id: camId,
        nc_program_name: v.nc_program_name.trim(),
        severity_id: v.severity_id,
        project_name: v.project_name?.trim() || null,
        part_name: v.part_name?.trim() || null,
        nc_line_reference: v.nc_line_reference?.trim() || null,
        expected_behavior: v.expected_behavior?.trim() || null,
        actual_behavior: v.actual_behavior?.trim() || null,
      })
      invalidateCaseEcosystem(qc, data.id)
      navigate(`/cases/${data.id}`)
    } catch (e: unknown) {
      const msg = String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? e)
      setError('nc_program_name', { message: msg })
    }
  }

  const errBinding = !!(formState.errors as { binding_id?: { message?: string } }).binding_id
  const errNc = !!(formState.errors as { nc_program_name?: { message?: string } }).nc_program_name
  const errSev = !!(formState.errors as { severity_id?: { message?: string } }).severity_id
  const errDesc = !!(formState.errors as { description?: { message?: string } }).description

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Schnell-Feedback vom Shopfloor
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Drei Schritte: <strong>1)</strong> Maschine und Programmumgebung wählen · <strong>2)</strong> betroffenes NC-Programm eintragen ·{' '}
        <strong>3)</strong> kurz beschreiben, was passiert ist. Optional können Sie unten weitere technische Details ergänzen.
      </Typography>
      {(bindings.data?.length ?? 0) === 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Für Ihre Maschine ist noch keine Freigabe hinterlegt. Bitte melden Sie das der IT / dem CAM-Team — unter{' '}
          <strong>Fertigungsbindungen</strong> muss eine Kombination aus Maschine, Steuerung und Postprozessor angelegt werden.
        </Alert>
      )}
      <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
        <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
          1. Wo arbeiten Sie?
        </Typography>
        <TextField
          select
          label="Maschine und Programmumgebung"
          fullWidth
          required
          error={errBinding}
          helperText={(formState.errors as { binding_id?: { message?: string } }).binding_id?.message}
          sx={{ mb: 2 }}
          {...register('binding_id')}
        >
          <MenuItem value="">
            <em>— bitte wählen —</em>
          </MenuItem>
          {(bindings.data ?? []).map((b) => (
            <MenuItem key={b.id} value={b.id}>
              {bindingLabel(b)}
            </MenuItem>
          ))}
        </TextField>

        <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
          2. Welches Programm betrifft es?
        </Typography>
        <Grid container spacing={2} sx={{ mb: 1 }}>
          <Grid size={{ xs: 12, md: 8 }}>
            <TextField
              label="NC-Programmname (wie an der Maschine / im Dateinamen)"
              fullWidth
              required
              autoComplete="off"
              error={errNc}
              helperText={
                (formState.errors as { nc_program_name?: { message?: string } }).nc_program_name?.message ??
                'Exakt der Name, unter dem Sie das Programm aufgerufen haben.'
              }
              {...register('nc_program_name')}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              select
              label="Wie dringend?"
              fullWidth
              required
              error={errSev}
              helperText={(formState.errors as { severity_id?: { message?: string } }).severity_id?.message}
              {...register('severity_id')}
            >
              <MenuItem value="">
                <em>— wählen —</em>
              </MenuItem>
              {(sev.data ?? []).map((s) => (
                <MenuItem key={s.id} value={s.id}>
                  {s.name}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
        </Grid>

        <Typography variant="subtitle2" color="primary" sx={{ mb: 1, mt: 1 }}>
          3. Was ist passiert?
        </Typography>
        <TextField
          label="Kurzbeschreibung (Pflicht)"
          fullWidth
          required
          multiline
          minRows={3}
          error={errDesc}
          helperText={(formState.errors as { description?: { message?: string } }).description?.message}
          placeholder="z. B. Abbruch in Zeile 42, Werkzeugwechsel hängt, unerwartete Bewegung …"
          {...register('description')}
        />
        <TextField
          label="Titel (optional — wenn leer, wird der Programmname verwendet)"
          fullWidth
          sx={{ mt: 2 }}
          {...register('title')}
        />

        <Accordion sx={{ mt: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle2">Weitere Angaben (optional)</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
              Nur ausfüllen, wenn Sie die Information parat haben. CAM-Modell nur ändern, wenn Sie den genauen Step kennen — sonst
              unverändert lassen.
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField label="Step- / CAM-Modell" select fullWidth defaultValue="" {...register('cam_step_model_id')}>
                  <MenuItem value="">
                    <em>Standard (Import / Altbestand)</em>
                  </MenuItem>
                  {(camSteps.data ?? []).map((s) => (
                    <MenuItem key={s.id} value={s.id}>
                      {s.code} — {s.name}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField label="Projektname" fullWidth {...register('project_name')} />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField label="Bauteil" fullWidth {...register('part_name')} />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField label="Satznummer / NC-Stelle" fullWidth {...register('nc_line_reference')} />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField label="Erwartetes Verhalten" fullWidth multiline minRows={2} {...register('expected_behavior')} />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField label="Tatsächliches Verhalten" fullWidth multiline minRows={2} {...register('actual_behavior')} />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        <Divider sx={{ my: 2 }} />
        <Button type="submit" variant="contained" size="large">
          Meldung absenden
        </Button>
      </Box>
    </Paper>
  )
}
