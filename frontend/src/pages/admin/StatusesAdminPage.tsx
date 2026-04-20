import { useMemo } from 'react'
import type { GridColDef } from '@mui/x-data-grid'
import { EntityCrudPage, type CrudField } from '../../components/crud/EntityCrudPage'

export function StatusesAdminPage() {
  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'key', headerName: 'Schlüssel', width: 140 },
      { field: 'name', headerName: 'Anzeigename', flex: 1, minWidth: 160 },
      { field: 'sort_order', headerName: 'Sortierung', width: 100, type: 'number' },
      { field: 'role_visibility', headerName: 'Sichtbarkeit', width: 160 },
    ],
    []
  )

  const fields: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'key', label: 'Schlüssel (technisch)', required: true },
      { kind: 'text', name: 'name', label: 'Anzeigename', required: true },
      { kind: 'number', name: 'sort_order', label: 'Sortierung', required: true },
      { kind: 'text', name: 'role_visibility', label: 'Rollen-Sichtbarkeit (optional)' },
    ],
    []
  )

  const fieldsEdit: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'name', label: 'Anzeigename', required: true },
      { kind: 'number', name: 'sort_order', label: 'Sortierung', required: true },
      { kind: 'text', name: 'role_visibility', label: 'Rollen-Sichtbarkeit (optional)' },
    ],
    []
  )

  return (
    <EntityCrudPage
      title="Status (Workflow)"
      resourceBase="/api/v1/statuses"
      queryKey={['statuses']}
      columns={columns}
      fields={fields}
      fieldsEdit={fieldsEdit}
    />
  )
}
