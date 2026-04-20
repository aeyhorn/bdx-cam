import { useMemo } from 'react'
import type { GridColDef } from '@mui/x-data-grid'
import { EntityCrudPage, type CrudField } from '../../components/crud/EntityCrudPage'

export function ControlSystemsAdminPage() {
  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'name', headerName: 'Name', flex: 1, minWidth: 160 },
      { field: 'version', headerName: 'Version', width: 120 },
      { field: 'notes', headerName: 'Notizen', flex: 1, minWidth: 200 },
    ],
    []
  )

  const fields: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'name', label: 'Name', required: true },
      { kind: 'text', name: 'version', label: 'Version' },
      { kind: 'text', name: 'notes', label: 'Notizen', multiline: true, rows: 3 },
    ],
    []
  )

  return (
    <EntityCrudPage
      title="Steuerungen"
      resourceBase="/api/v1/control-systems"
      queryKey={['control-systems']}
      columns={columns}
      fields={fields}
    />
  )
}
