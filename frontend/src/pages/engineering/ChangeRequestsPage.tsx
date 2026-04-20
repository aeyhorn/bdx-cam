import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { GridColDef } from '@mui/x-data-grid'
import { api } from '../../api/client'
import { EntityCrudPage, type CrudField } from '../../components/crud/EntityCrudPage'

type Assignee = { id: number; first_name: string; last_name: string; email: string }
type PV = { id: number; name: string; version: string }

export function ChangeRequestsPage() {
  const assignees = useQuery({
    queryKey: ['assignees'],
    queryFn: async () => (await api.get<Assignee[]>('/api/v1/users/assignees')).data,
  })
  const pvs = useQuery({
    queryKey: ['post-versions'],
    queryFn: async () => (await api.get<PV[]>('/api/v1/post-versions')).data,
  })

  const ownerOpts = useMemo(
    () => [
      { value: '', label: '— kein Owner —' },
      ...(assignees.data ?? []).map((u) => ({
        value: u.id,
        label: `${u.first_name} ${u.last_name}`,
      })),
    ],
    [assignees.data]
  )
  const pvOpts = useMemo(
    () => [
      { value: '', label: '— keine Post-Version —' },
      ...(pvs.data ?? []).map((p) => ({ value: p.id, label: `${p.name} ${p.version}` })),
    ],
    [pvs.data]
  )

  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'change_no', headerName: 'CR-Nr.', width: 120 },
      { field: 'title', headerName: 'Titel', flex: 1, minWidth: 200 },
      { field: 'status', headerName: 'Status', width: 100 },
      { field: 'created_at', headerName: 'Erstellt', width: 180 },
    ],
    []
  )

  const fields: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'title', label: 'Titel', required: true },
      { kind: 'text', name: 'description', label: 'Beschreibung', multiline: true, rows: 3 },
      { kind: 'text', name: 'status', label: 'Status (z. B. open, in_progress, done)', required: true },
      {
        kind: 'select',
        name: 'owner_id',
        label: 'Owner',
        required: false,
        options: ownerOpts,
        coerceNumber: true,
      },
      {
        kind: 'select',
        name: 'post_processor_version_id',
        label: 'Post-Version',
        required: false,
        options: pvOpts,
        coerceNumber: true,
      },
      { kind: 'text', name: 'cps_reference', label: 'CPS-Referenz' },
      { kind: 'text', name: 'target_behavior', label: 'Zielverhalten', multiline: true, rows: 2 },
      { kind: 'text', name: 'technical_solution', label: 'Technische Lösung', multiline: true, rows: 2 },
      { kind: 'text', name: 'risk_notes', label: 'Risiko / Hinweise', multiline: true, rows: 2 },
    ],
    [ownerOpts, pvOpts]
  )

  return (
    <EntityCrudPage
      title="Change Requests"
      resourceBase="/api/v1/change-requests"
      queryKey={['change-requests']}
      columns={columns}
      fields={fields}
    />
  )
}
