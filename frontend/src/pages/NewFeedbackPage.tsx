import { useQuery } from '@tanstack/react-query'
import { Box, Button, Divider, MenuItem, Paper, TextField, Typography } from '@mui/material'
import Grid from '@mui/material/Grid'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { api } from '../api/client'

const schema = z.object({
  title: z.string().min(1),
  machine_id: z.coerce.number(),
  post_processor_version_id: z.coerce.number(),
  nc_program_name: z.string().min(1),
  description: z.string().optional(),
  severity_id: z.coerce.number(),
  control_system_id: z.preprocess(
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
  const machines = useQuery({
    queryKey: ['machines'],
    queryFn: async () => (await api.get('/api/v1/machines')).data,
  })
  const posts = useQuery({
    queryKey: ['posts'],
    queryFn: async () => (await api.get('/api/v1/post-versions')).data,
  })
  const sev = useQuery({
    queryKey: ['sev'],
    queryFn: async () => (await api.get('/api/v1/severities')).data,
  })
  const cs = useQuery({
    queryKey: ['cs'],
    queryFn: async () => (await api.get('/api/v1/control-systems')).data,
  })

  const { register, handleSubmit, formState, setError } = useForm<Record<string, unknown>>({
    defaultValues: {},
  })

  async function onSubmit(raw: Record<string, unknown>) {
    const parsed = schema.safeParse(raw)
    if (!parsed.success) {
      setError('title', { message: 'Eingaben prüfen' })
      return
    }
    const values = parsed.data
    const { data } = await api.post('/api/v1/cases', {
      ...values,
      control_system_id: values.control_system_id ?? null,
    })
    navigate(`/cases/${data.id}`)
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Neues Feedback
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Bereich 1: Schnellmeldung · Bereich 2: Details
      </Typography>
      <Box component="form" onSubmit={handleSubmit(onSubmit)}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 6 }}>
            <TextField label="Titel" fullWidth required {...register('title')} error={!!(formState.errors as { title?: unknown }).title} />
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <TextField label="Severity" select fullWidth required defaultValue="" {...register('severity_id')}>
              {(sev.data ?? []).map((s: { id: number; name: string }) => (
                <MenuItem key={s.id} value={s.id}>
                  {s.name}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <TextField label="Maschine" select fullWidth required defaultValue="" {...register('machine_id')}>
              {(machines.data ?? []).map((m: { id: number; name: string }) => (
                <MenuItem key={m.id} value={m.id}>
                  {m.name}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <TextField label="Post-Version" select fullWidth required defaultValue="" {...register('post_processor_version_id')}>
              {(posts.data ?? []).map((p: { id: number; name: string; version: string }) => (
                <MenuItem key={p.id} value={p.id}>
                  {p.name} {p.version}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <TextField label="NC-Programmname" fullWidth required {...register('nc_program_name')} />
          </Grid>
          <Grid size={{ xs: 12 }}>
            <TextField label="Kurzbeschreibung" fullWidth multiline minRows={2} {...register('description')} />
          </Grid>
        </Grid>
        <Divider sx={{ my: 2 }} />
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 6 }}>
            <TextField label="Steuerung" select fullWidth defaultValue="" {...register('control_system_id')}>
              <MenuItem value="">—</MenuItem>
              {(cs.data ?? []).map((x: { id: number; name: string }) => (
                <MenuItem key={x.id} value={x.id}>
                  {x.name}
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
            <TextField label="Satznummer / NC-Bereich" fullWidth {...register('nc_line_reference')} />
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <TextField label="Erwartetes Verhalten" fullWidth multiline minRows={3} {...register('expected_behavior')} />
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <TextField label="Tatsächliches Verhalten" fullWidth multiline minRows={3} {...register('actual_behavior')} />
          </Grid>
        </Grid>
        <Box sx={{ mt: 2 }}>
          <Button type="submit" variant="contained">
            Fall anlegen
          </Button>
        </Box>
      </Box>
    </Paper>
  )
}
