import { useMemo } from 'react'
import type { GridColDef } from '@mui/x-data-grid'
import { EntityCrudPage, type CrudField } from '../../components/crud/EntityCrudPage'

export function CamStepModelsAdminPage() {
  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'code', headerName: 'Code', width: 140 },
      { field: 'name', headerName: 'Bezeichnung', flex: 1, minWidth: 200 },
      { field: 'revision', headerName: 'Rev.', width: 90 },
    ],
    []
  )

  const fields: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'code', label: 'Eindeutiger Code (z. B. PDM-ID)', required: true },
      { kind: 'text', name: 'name', label: 'Name / Teil', required: true },
      { kind: 'text', name: 'revision', label: 'Revision' },
      { kind: 'text', name: 'notes', label: 'Notizen', multiline: true, rows: 2 },
    ],
    []
  )

  return (
    <EntityCrudPage
      title="Step- / CAM-Modelle"
      resourceBase="/api/v1/cam-step-models"
      queryKey={['cam-step-models']}
      columns={columns}
      fields={fields}
      fieldsEdit={[
        { kind: 'text', name: 'name', label: 'Name / Teil', required: true },
        { kind: 'text', name: 'revision', label: 'Revision' },
        { kind: 'text', name: 'notes', label: 'Notizen', multiline: true, rows: 2 },
      ]}
    />
  )
}
