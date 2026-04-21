import {
  Alert,
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { api } from '../../api/client'
import { invalidateAfterEntityWrite } from '../../lib/queryCache'

export type CrudField =
  | { kind: 'text'; name: string; label: string; required?: boolean; multiline?: boolean; rows?: number }
  | { kind: 'email' | 'password'; name: string; label: string; required?: boolean; helperCreate?: string }
  | { kind: 'number'; name: string; label: string; required?: boolean }
  | { kind: 'checkbox'; name: string; label: string }
  | {
      kind: 'select'
      name: string
      label: string
      required?: boolean
      options: { value: string | number; label: string }[]
      emptyLabel?: string
      /** coerce MenuItem string values to number for API */
      coerceNumber?: boolean
    }
  | { kind: 'date'; name: string; label: string; required?: boolean }

export type EntityCrudPageProps = {
  title: string
  /** e.g. /api/v1/machines — no trailing slash */
  resourceBase: string
  queryKey: string[]
  columns: GridColDef[]
  fields: CrudField[]
  /** If set, used in edit dialog instead of `fields` (e.g. omit immutable keys). */
  fieldsEdit?: CrudField[]
  /** Field names omitted when unchanged on edit (e.g. optional password) */
  omitEmptyOnEdit?: string[]
  canCreate?: boolean
  canEdit?: boolean
  canDelete?: boolean
  headerActions?: ReactNode
  onRowDoubleClick?: (row: Record<string, unknown>) => void
}

export function EntityCrudPage({
  title,
  resourceBase,
  queryKey,
  columns,
  fields,
  fieldsEdit,
  omitEmptyOnEdit = [],
  canCreate = true,
  canEdit = true,
  canDelete = true,
  headerActions,
  onRowDoubleClick,
}: EntityCrudPageProps) {
  const qc = useQueryClient()
  const [err, setErr] = useState<string | null>(null)
  const [delId, setDelId] = useState<number | null>(null)
  const [open, setOpen] = useState<'create' | 'edit' | null>(null)
  const [editRow, setEditRow] = useState<Record<string, unknown> | null>(null)

  const activeFields = open === 'edit' && fieldsEdit ? fieldsEdit : fields

  const list = useQuery({
    queryKey,
    queryFn: async () => (await api.get<Record<string, unknown>[]>(resourceBase)).data,
  })

  const defaults = useMemo(() => {
    const d: Record<string, unknown> = {}
    const src = fieldsEdit ? [...fields, ...fieldsEdit] : fields
    const seen = new Set<string>()
    for (const f of src) {
      if (seen.has(f.name)) continue
      seen.add(f.name)
      if (f.kind === 'checkbox') d[f.name] = false
      else if (f.kind === 'number') d[f.name] = ''
      else d[f.name] = ''
    }
    return d
  }, [fields, fieldsEdit])

  const { register, handleSubmit, reset, setValue, watch } = useForm<Record<string, unknown>>({ defaultValues: defaults })

  useEffect(() => {
    if (open === 'edit' && editRow) {
      const next: Record<string, unknown> = { ...defaults }
      const fs = fieldsEdit ?? fields
      for (const f of fs) {
        let v = editRow[f.name]
        if (f.kind === 'date' && typeof v === 'string' && v.includes('T')) v = v.slice(0, 10)
        if (v !== undefined && v !== null) next[f.name] = v
      }
      reset(next)
    }
    if (open === 'create') {
      reset(defaults)
    }
  }, [open, editRow, reset, defaults, fields, fieldsEdit])

  const invalidate = useCallback(() => {
    invalidateAfterEntityWrite(qc, resourceBase, queryKey)
  }, [qc, queryKey, resourceBase])

  const createMut = useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      await api.post(resourceBase, body)
    },
    onSuccess: () => {
      setOpen(null)
      setErr(null)
      invalidate()
    },
    onError: (e: unknown) => setErr(extractErr(e)),
  })

  const patchMut = useMutation({
    mutationFn: async ({ id, body }: { id: number; body: Record<string, unknown> }) => {
      await api.patch(`${resourceBase}/${id}`, body)
    },
    onSuccess: () => {
      setOpen(null)
      setEditRow(null)
      setErr(null)
      invalidate()
    },
    onError: (e: unknown) => setErr(extractErr(e)),
  })

  const deleteMut = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`${resourceBase}/${id}`)
    },
    onSuccess: () => {
      setDelId(null)
      setErr(null)
      invalidate()
    },
    onError: (e: unknown) => setErr(extractErr(e)),
  })

  const actionCol: GridColDef = {
    field: '__actions',
    headerName: '',
    width: 160,
    sortable: false,
    renderCell: (p: GridRenderCellParams) => (
      <Stack direction="row" spacing={0.5}>
        {canEdit && (
          <Button size="small" onClick={() => onEditClick(p.row as Record<string, unknown>)}>
            Bearbeiten
          </Button>
        )}
        {canDelete && (
          <Button size="small" color="error" onClick={() => setDelId(p.row.id as number)}>
            Löschen
          </Button>
        )}
      </Stack>
    ),
  }

  const displayCols = useMemo(() => {
    if (!canEdit && !canDelete) return columns
    return [...columns, actionCol]
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [columns, canEdit, canDelete])

  function onEditClick(row: Record<string, unknown>) {
    setEditRow(row)
    setOpen('edit')
    setErr(null)
  }

  function normalizeBody(raw: Record<string, unknown>, mode: 'create' | 'edit'): Record<string, unknown> {
    const out: Record<string, unknown> = {}
    const fs = mode === 'edit' && fieldsEdit ? fieldsEdit : fields
    for (const f of fs) {
      let v = raw[f.name]
      if (f.kind === 'select') {
        if ((v === '' || v === undefined) && !f.required) {
          out[f.name] = null
          continue
        }
        if (f.coerceNumber && v !== '' && v !== undefined && v !== null) {
          v = Number(v)
        }
      }
      if (f.kind === 'number') {
        if (v === '' || v === undefined) {
          if (f.required) continue
          v = null
        } else v = Number(v)
      }
      if (f.kind === 'date' && v === '') {
        v = null
      }
      if (f.kind === 'password' && mode === 'edit' && (!v || v === '')) {
        continue
      }
      if (f.kind === 'checkbox') {
        out[f.name] = Boolean(v)
        continue
      }
      if (mode === 'edit' && omitEmptyOnEdit.includes(f.name) && (v === '' || v === undefined)) continue
      out[f.name] = v
    }
    return out
  }

  function onSave(raw: Record<string, unknown>) {
    const mode = open === 'edit' ? 'edit' : 'create'
    const body = normalizeBody(raw, mode)
    if (open === 'edit' && editRow?.id != null) {
      patchMut.mutate({ id: editRow.id as number, body })
    } else {
      createMut.mutate(body)
    }
  }

  return (
    <Box>
      <Stack direction="row" spacing={2} sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{title}</Typography>
        <Stack direction="row" spacing={1}>
          {headerActions}
          {canCreate && (
            <Button variant="contained" onClick={() => { setEditRow(null); setOpen('create'); setErr(null) }}>
              Neu anlegen
            </Button>
          )}
        </Stack>
      </Stack>
      {err && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setErr(null)}>
          {err}
        </Alert>
      )}
      <Box sx={{ height: '65vh', minHeight: 420, width: '100%', bgcolor: 'background.paper' }}>
        <DataGrid
          rows={(list.data as { id: number }[]) ?? []}
          columns={displayCols}
          loading={list.isLoading}
          getRowId={(r) => r.id as number}
          density="compact"
          rowHeight={34}
          columnHeaderHeight={36}
          disableRowSelectionOnClick
          onRowDoubleClick={(params) => onRowDoubleClick?.(params.row as Record<string, unknown>)}
          sx={{ fontSize: 12 }}
        />
      </Box>

      <Dialog open={open !== null} onClose={() => setOpen(null)} maxWidth="sm" fullWidth>
        <DialogTitle>{open === 'edit' ? 'Bearbeiten' : 'Neu anlegen'}</DialogTitle>
        <form onSubmit={handleSubmit(onSave)}>
          <DialogContent>
            <Stack spacing={2} sx={{ pt: 1 }}>
              {activeFields.map((f) => {
                if (f.kind === 'select') {
                  const hasExplicitEmpty = f.options.some((o) => o.value === '' || o.value === null)
                  const current = watch(f.name)
                  return (
                    <TextField
                      key={f.name}
                      select
                      label={f.label}
                      fullWidth
                      required={f.required}
                      value={current == null ? '' : (current as string | number)}
                      onChange={(e) => setValue(f.name, e.target.value)}
                    >
                      {!hasExplicitEmpty && (f.emptyLabel !== undefined || !f.required) && (
                        <MenuItem value="">
                          <em>{f.emptyLabel ?? '—'}</em>
                        </MenuItem>
                      )}
                      {f.options.map((o) => (
                        <MenuItem key={String(o.value)} value={o.value as string | number}>
                          {o.label}
                        </MenuItem>
                      ))}
                    </TextField>
                  )
                }
                if (f.kind === 'checkbox') {
                  return (
                    <FormControlLabel
                      key={f.name}
                      control={<Checkbox checked={Boolean(watch(f.name))} onChange={(_, c) => setValue(f.name, c)} />}
                      label={f.label}
                    />
                  )
                }
                if (f.kind === 'date') {
                  return (
                    <TextField
                      key={f.name}
                      label={f.label}
                      type="date"
                      fullWidth
                      required={f.required}
                      slotProps={{ inputLabel: { shrink: true } }}
                      {...register(f.name)}
                    />
                  )
                }
                return (
                  <TextField
                    key={f.name}
                    label={f.label}
                    type={f.kind === 'number' ? 'number' : f.kind === 'password' ? 'password' : f.kind === 'email' ? 'email' : 'text'}
                    fullWidth
                    required={open === 'create' ? f.required : f.kind === 'password' ? false : f.required}
                    multiline={f.kind === 'text' ? f.multiline : false}
                    minRows={f.kind === 'text' ? f.rows : undefined}
                    helperText={f.kind === 'password' && open === 'create' ? f.helperCreate : undefined}
                    {...register(f.name)}
                  />
                )
              })}
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(null)}>Abbrechen</Button>
            <Button type="submit" variant="contained" disabled={createMut.isPending || patchMut.isPending}>
              Speichern
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      <Dialog open={delId !== null} onClose={() => setDelId(null)}>
        <DialogTitle>Eintrag löschen?</DialogTitle>
        <DialogContent>
          <Typography variant="body2">Dieser Vorgang kann je nach Entität nicht rückgängig gemacht werden.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDelId(null)}>Abbrechen</Button>
          <Button color="error" variant="contained" disabled={deleteMut.isPending} onClick={() => delId != null && deleteMut.mutate(delId)}>
            Löschen
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

function extractErr(e: unknown): string {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const ax = e as any
  const d = ax?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x.msg ?? JSON.stringify(x)).join('; ')
  return ax?.message ?? 'Anfrage fehlgeschlagen'
}
