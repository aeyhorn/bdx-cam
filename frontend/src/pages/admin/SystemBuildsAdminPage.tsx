import { useMemo } from 'react'
import type { GridColDef } from '@mui/x-data-grid'
import { EntityCrudPage, type CrudField } from '../../components/crud/EntityCrudPage'

export function SystemBuildsAdminPage() {
  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'component', headerName: 'Softwareteil', width: 160 },
      { field: 'build_no', headerName: 'Build', width: 90, type: 'number' },
      { field: 'version_label', headerName: 'Version', width: 130 },
      { field: 'is_deployed', headerName: 'Im Einsatz', width: 100, type: 'boolean' },
      { field: 'created_at', headerName: 'Erstellt', width: 180 },
    ],
    []
  )

  const fields: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'component', label: 'Softwareteil (z. B. backend-api)', required: true },
      { kind: 'text', name: 'version_label', label: 'Versionslabel (z. B. 1.3.7)', required: true },
      { kind: 'checkbox', name: 'is_deployed', label: 'Aktuell im Einsatz' },
      { kind: 'text', name: 'changelog', label: 'Änderungen', multiline: true, rows: 3 },
    ],
    []
  )

  return (
    <EntityCrudPage
      title="System-Build-Versionen"
      resourceBase="/api/v1/system-builds"
      queryKey={['system-builds']}
      columns={columns}
      fields={fields}
      fieldsEdit={fields}
    />
  )
}
