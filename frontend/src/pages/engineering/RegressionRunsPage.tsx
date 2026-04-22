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

type TC = { id: number; title: string }
type PV = { id: number; name: string; version: string }
type Row = {
  id: number
  test_case_id: number
  post_processor_version_id: number
  result: string
  notes: string | null
  executed_at: string | null
}

const results = [
  { value: 'open', label: 'Offen' },
  { value: 'passed', label: 'Bestanden' },
  { value: 'failed', label: 'Fehlgeschlagen' },
  { value: 'partial', label: 'Teilweise' },
]

export function RegressionRunsPage() {
  const qc = useQueryClient()
  const [err, setErr] = useState<string | null>(null)
  const [open, setOpen] = useState(false)
  const [editRow, setEditRow] = useState<Row | null>(null)
  const [delId, setDelId] = useState<number | null>(null)

  const list = useQuery({
    queryKey: ['regression-runs'],
    queryFn: async () => (await api.get<Row[]>('/api/v1/regression-runs')).data,
  })
  const tcs = useQuery({
    queryKey: ['test-cases'],
    queryFn: async () => (await api.get<TC[]>('/api/v1/test-cases')).data,
  })
  const pvs = useQuery({
    queryKey: ['post-versions'],
    queryFn: async () => (await api.get<PV[]>('/api/v1/post-versions')).data,
  })

  const [fTc, setFTc] = useState('')
  const [fPv, setFPv] = useState('')
  const [fRes, setFRes] = useState('open')
  const [fNotes, setFNotes] = useState('')

  const invalidate = () => invalidateAfterEntityWrite(qc, '/api/v1/regression-runs', ['regression-runs'])

  const createMut = useMutation({
    mutationFn: async () => {
      await api.post('/api/v1/regression-runs', {
        test_case_id: Number(fTc),
        post_processor_version_id: Number(fPv),
        result: fRes,
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

  const patchMut = useMutation({
    mutationFn: async () => {
      if (!editRow) return
      await api.patch(`/api/v1/regression-runs/${editRow.id}`, {
        result: fRes,
        notes: fNotes || null,
      })
    },
    onSuccess: () => {
      setEditRow(null)
      setErr(null)
      invalidate()
    },
    onError: (e: unknown) => setErr(String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? e)),
  })

  const delMut = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/v1/regression-runs/${id}`)
    },
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
      { field: 'test_case_id', headerName: 'Programmierfall-ID', width: 130 },
      { field: 'post_processor_version_id', headerName: 'Post-V.', width: 100 },
      { field: 'result', headerName: 'Ergebnis', width: 110 },
      { field: 'notes', headerName: 'Notizen', flex: 1, minWidth: 160 },
      { field: 'executed_at', headerName: 'Ausgeführt', width: 180 },
      {
        field: '__a',
        headerName: '',
        width: 160,
        sortable: false,
        renderCell: (p: GridRenderCellParams<Row>) => (
          <Stack direction="row" spacing={0.5}>
            <Button
              size="small"
              onClick={() => {
                const r = p.row
                setEditRow(r)
                setFRes(r.result)
                setFNotes(r.notes ?? '')
              }}
            >
              Bearbeiten
            </Button>
            <Button size="small" color="error" onClick={() => setDelId(p.row.id)}>
              Löschen
            </Button>
          </Stack>
        ),
      },
    ],
    []
  )

  return (
    <Box>
      <Stack direction="row" spacing={2} sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Regression Runs</Typography>
        <Button
          variant="contained"
          onClick={() => {
            setOpen(true)
            setFTc('')
            setFPv('')
            setFRes('open')
            setFNotes('')
            setErr(null)
          }}
        >
          Neu (Maschinentest)
        </Button>
      </Stack>
      {err && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setErr(null)}>
          {err}
        </Alert>
      )}
      <Box sx={{ height: '65vh', minHeight: 420, bgcolor: 'background.paper' }}>
        <DataGrid rows={list.data ?? []} columns={columns} loading={list.isLoading} getRowId={(r) => r.id} density="compact" rowHeight={34} columnHeaderHeight={36} disableRowSelectionOnClick sx={{ fontSize: 12 }} />
      </Box>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Regression dokumentieren</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <TextField select label="Programmierfall" required fullWidth value={fTc} onChange={(e) => setFTc(e.target.value)}>
              {(tcs.data ?? []).map((t) => (
                <MenuItem key={t.id} value={t.id}>
                  {t.title}
                </MenuItem>
              ))}
            </TextField>
            <TextField select label="Post-Version (auf Maschine)" required fullWidth value={fPv} onChange={(e) => setFPv(e.target.value)}>
              {(pvs.data ?? []).map((p) => (
                <MenuItem key={p.id} value={p.id}>
                  {p.name} {p.version}
                </MenuItem>
              ))}
            </TextField>
            <TextField select label="Ergebnis" fullWidth value={fRes} onChange={(e) => setFRes(e.target.value)}>
              {results.map((r) => (
                <MenuItem key={r.value} value={r.value}>
                  {r.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField label="Notizen" fullWidth multiline minRows={2} value={fNotes} onChange={(e) => setFNotes(e.target.value)} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Abbrechen</Button>
          <Button variant="contained" disabled={!fTc || !fPv || createMut.isPending} onClick={() => createMut.mutate()}>
            Speichern
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={editRow !== null} onClose={() => setEditRow(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Regression bearbeiten</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <TextField select label="Ergebnis" fullWidth value={fRes} onChange={(e) => setFRes(e.target.value)}>
              {results.map((r) => (
                <MenuItem key={r.value} value={r.value}>
                  {r.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField label="Notizen" fullWidth multiline minRows={2} value={fNotes} onChange={(e) => setFNotes(e.target.value)} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditRow(null)}>Abbrechen</Button>
          <Button variant="contained" disabled={patchMut.isPending} onClick={() => patchMut.mutate()}>
            Speichern
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={delId !== null} onClose={() => setDelId(null)}>
        <DialogTitle>Eintrag löschen?</DialogTitle>
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
