import { useMemo } from 'react'
import type { GridColDef } from '@mui/x-data-grid'
import { EntityCrudPage, type CrudField } from '../../components/crud/EntityCrudPage'

export function CategoriesAdminPage() {
  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'name', headerName: 'Name', flex: 1, minWidth: 200 },
      { field: 'description', headerName: 'Beschreibung', flex: 1, minWidth: 240 },
    ],
    []
  )

  const fields: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'name', label: 'Name', required: true },
      { kind: 'text', name: 'description', label: 'Beschreibung', multiline: true, rows: 3 },
    ],
    []
  )

  return (
    <EntityCrudPage
      title="Fehlerkategorien"
      resourceBase="/api/v1/categories"
      queryKey={['categories']}
      columns={columns}
      fields={fields}
    />
  )
}
