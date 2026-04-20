import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { api } from '../../api/client'
import { invalidateAfterEntityWrite } from '../../lib/queryCache'

type BindingRow = {
  id: number
  machine_id: number
  post_processor_version_id: number
  control_system_id: number
  notes: string | null
  machine?: { name: string }
  post_processor_version?: { name: string; version: string }
  control_system?: { name: string }
}

export function MachinePostBindingsAdminPage() {
  const qc = useQueryClient()
  const [err, setErr] = useState<string | null>(null)
  const [open, setOpen] = useState(false)
  const [delId, setDelId] = useState<number | null>(null)
  const [fM, setFM] = useState('')
  const [fP, setFP] = useState('')
  const [fC, setFC] = useState('')
  const [fNotes, setFNotes] = useState('')

  const list = useQuery({
    queryKey: ['machine-post-bindings'],
    queryFn: async () => (await api.get<BindingRow[]>('/api/v1/machine-post-bindings')).data,
  })
  const machines = useQuery({
    queryKey: ['machines'],
    queryFn: async () => (await api.get<{ id: number; name: string }[]>('/api/v1/machines')).data,
  })
  const posts = useQuery({
    queryKey: ['post-versions'],
    queryFn: async () => (await api.get<{ id: number; name: string; version: string }[]>('/api/v1/post-versions')).data,
  })
  const controls = useQuery({
    queryKey: ['control-systems'],
    queryFn: async () => (await api.get<{ id: number; name: string }[]>('/api/v1/control-systems')).data,
  })

  const invalidate = () => invalidateAfterEntityWrite(qc, '/api/v1/machine-post-bindings', ['machine-post-bindings'])

  const createMut = useMutation({
    mutationFn: async () => {
      await api.post('/api/v1/machine-post-bindings', {
        machine_id: Number(fM),
        post_processor_version_id: Number(fP),
        control_system_id: Number(fC),
        notes: fNotes || null,
      })
    },
    onSuccess: () => {
      setOpen(false)
      setErr(null)
      setFNotes('')
      invalidate()
    },
    onError: (e: unknown) => setErr(String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? e)),
  })

  const delMut = useMutation({
    mutationFn: async (id: number) => api.delete(`/api/v1/machine-post-bindings/${id}`),
    onSuccess: () => {
      setDelId(null)
      setErr(null)
      invalidate()
    },
    onError: (e: unknown) => setErr(String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? e)),
  })

  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      {
        field: 'machine_id',
        headerName: 'Maschine',
        flex: 1,
        minWidth: 140,
        valueGetter: (_v, row) => row.machine?.name ?? row.machine_id,
      },
      {
        field: 'post_processor_version_id',
        headerName: 'Postprozessor',
        flex: 1,
        minWidth: 160,
        valueGetter: (_v, row) =>
          row.post_processor_version ? `${row.post_processor_version.name} ${row.post_processor_version.version}` : row.post_processor_version_id,
      },
      {
        field: 'control_system_id',
        headerName: 'Steuerung',
        flex: 1,
        minWidth: 120,
        valueGetter: (_v, row) => row.control_system?.name ?? row.control_system_id,
      },
      {
        field: '__a',
        headerName: '',
        width: 100,
        sortable: false,
        renderCell: (p: GridRenderCellParams<BindingRow>) => (
          <Button size="small" color="error" onClick={() => setDelId(p.row.id)}>
            Löschen
          </Button>
        ),
      },
    ],
    []
  )

  return (
    <Box>
      <Stack direction="row" spacing={2} sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Fertigungsbindungen</Typography>
        <Button
          variant="contained"
          onClick={() => {
            setOpen(true)
            setFM('')
            setFP('')
            setFC('')
            setFNotes('')
            setErr(null)
          }}
        >
          Freigabe anlegen
        </Button>
      </Stack>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Jede Zeile ist eine <strong>eindeutig freigegebene</strong> Kombination aus Maschine, Steuerung und Postprozessor-Version. Nur so konfigurierte
        Triplets sind bei neuem Feedback und bei Änderungen an Fällen erlaubt.
      </Typography>
      {err && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setErr(null)}>
          {err}
        </Alert>
      )}
      <Box sx={{ height: '65vh', minHeight: 420, bgcolor: 'background.paper' }}>
        <DataGrid rows={list.data ?? []} columns={columns} loading={list.isLoading} getRowId={(r) => r.id} density="compact" rowHeight={34} columnHeaderHeight={36} disableRowSelectionOnClick sx={{ fontSize: 12 }} />
      </Box>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Freigabe (Maschine · Steuerung · Post)</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <TextField select label="Maschine" required fullWidth value={fM} onChange={(e) => setFM(e.target.value)}>
              {(machines.data ?? []).map((m) => (
                <MenuItem key={m.id} value={m.id}>
                  {m.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField select label="Postprozessor-Version" required fullWidth value={fP} onChange={(e) => setFP(e.target.value)}>
              {(posts.data ?? []).map((p) => (
                <MenuItem key={p.id} value={p.id}>
                  {p.name} {p.version}
                </MenuItem>
              ))}
            </TextField>
            <TextField select label="Steuerung" required fullWidth value={fC} onChange={(e) => setFC(e.target.value)}>
              {(controls.data ?? []).map((x) => (
                <MenuItem key={x.id} value={x.id}>
                  {x.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField label="Notizen" fullWidth multiline minRows={2} value={fNotes} onChange={(e) => setFNotes(e.target.value)} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Abbrechen</Button>
          <Button variant="contained" disabled={!fM || !fP || !fC || createMut.isPending} onClick={() => createMut.mutate()}>
            Speichern
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={delId !== null} onClose={() => setDelId(null)}>
        <DialogTitle>Freigabe löschen?</DialogTitle>
        <DialogActions>
          <Button onClick={() => setDelId(null)}>Abbrechen</Button>
          <Button color="error" variant="contained" onClick={() => delId != null && delMut.mutate(delId)}>
            Löschen
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
