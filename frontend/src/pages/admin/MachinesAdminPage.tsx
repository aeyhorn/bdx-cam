import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { GridColDef } from '@mui/x-data-grid'
import { api } from '../../api/client'
import { EntityCrudPage, type CrudField } from '../../components/crud/EntityCrudPage'

type CS = { id: number; name: string; version?: string | null }

export function MachinesAdminPage() {
  const cs = useQuery({
    queryKey: ['control-systems'],
    queryFn: async () => (await api.get<CS[]>('/api/v1/control-systems')).data,
  })

  const csOpts = useMemo(
    () => [{ value: '', label: '— keine Steuerung —' }, ...(cs.data ?? []).map((x) => ({ value: x.id, label: `${x.name}${x.version ? ` (${x.version})` : ''}` }))],
    [cs.data]
  )

  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'name', headerName: 'Name', flex: 1, minWidth: 160 },
      { field: 'manufacturer', headerName: 'Hersteller', width: 130 },
      { field: 'model', headerName: 'Modell', width: 120 },
      {
        field: 'control_system',
        headerName: 'Steuerung',
        width: 160,
        valueGetter: (_v, row) => (row as { control_system?: { name: string } }).control_system?.name ?? '',
      },
      { field: 'location', headerName: 'Standort', width: 120 },
      { field: 'is_active', headerName: 'Aktiv', width: 80, type: 'boolean' },
    ],
    []
  )

  const fields: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'name', label: 'Name', required: true },
      { kind: 'text', name: 'manufacturer', label: 'Hersteller' },
      { kind: 'text', name: 'model', label: 'Modell' },
      { kind: 'text', name: 'location', label: 'Standort' },
      { kind: 'text', name: 'notes', label: 'Notizen', multiline: true, rows: 2 },
      {
        kind: 'select',
        name: 'control_system_id',
        label: 'Steuerung',
        required: false,
        options: csOpts,
        coerceNumber: true,
      },
      { kind: 'checkbox', name: 'is_active', label: 'Aktiv' },
    ],
    [csOpts]
  )

  return (
    <EntityCrudPage
      title="Maschinen"
      resourceBase="/api/v1/machines"
      queryKey={['machines']}
      columns={columns}
      fields={fields}
    />
  )
}
