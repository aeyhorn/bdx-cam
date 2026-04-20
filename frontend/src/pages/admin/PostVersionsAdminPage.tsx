import { useMemo } from 'react'
import type { GridColDef } from '@mui/x-data-grid'
import { EntityCrudPage, type CrudField } from '../../components/crud/EntityCrudPage'

const statusOpts = [
  { value: 'draft', label: 'Entwurf' },
  { value: 'released', label: 'Released' },
  { value: 'deprecated', label: 'Deprecated' },
]

export function PostVersionsAdminPage() {
  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'name', headerName: 'Name', width: 160 },
      { field: 'version', headerName: 'Version', width: 100 },
      { field: 'machine_family', headerName: 'Familie', width: 140 },
      { field: 'status', headerName: 'Status', width: 110 },
      { field: 'is_productive', headerName: 'Produktiv', width: 100, type: 'boolean' },
    ],
    []
  )

  const fields: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'name', label: 'Name', required: true },
      { kind: 'text', name: 'version', label: 'Version', required: true },
      { kind: 'text', name: 'machine_family', label: 'Maschinenfamilie', required: true },
      { kind: 'text', name: 'description', label: 'Beschreibung', multiline: true, rows: 2 },
      { kind: 'select', name: 'status', label: 'Status', required: true, options: statusOpts },
      { kind: 'checkbox', name: 'is_productive', label: 'Produktiv freigegeben' },
      { kind: 'date', name: 'release_date', label: 'Release-Datum' },
      { kind: 'text', name: 'notes', label: 'Notizen', multiline: true, rows: 2 },
    ],
    []
  )

  return (
    <EntityCrudPage
      title="Post-Versionen"
      resourceBase="/api/v1/post-versions"
      queryKey={['post-versions']}
      columns={columns}
      fields={fields}
    />
  )
}
