import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { GridColDef } from '@mui/x-data-grid'
import { api } from '../../api/client'
import { EntityCrudPage, type CrudField } from '../../components/crud/EntityCrudPage'

type Cat = { id: number; name: string }

export function KnowledgePage() {
  const cats = useQuery({
    queryKey: ['categories'],
    queryFn: async () => (await api.get<Cat[]>('/api/v1/categories')).data,
  })

  const catOpts = useMemo(
    () => [{ value: '', label: '— keine Kategorie —' }, ...(cats.data ?? []).map((c) => ({ value: c.id, label: c.name }))],
    [cats.data]
  )

  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'title', headerName: 'Titel', flex: 1, minWidth: 200 },
      { field: 'symptom', headerName: 'Symptom', width: 160 },
      { field: 'updated_at', headerName: 'Aktualisiert', width: 180 },
    ],
    []
  )

  const fields: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'title', label: 'Titel', required: true },
      { kind: 'text', name: 'symptom', label: 'Symptom', multiline: true, rows: 2 },
      { kind: 'text', name: 'cause', label: 'Ursache', multiline: true, rows: 2 },
      { kind: 'text', name: 'resolution', label: 'Lösung', multiline: true, rows: 2 },
      { kind: 'select', name: 'error_category_id', label: 'Fehlerkategorie', required: false, options: catOpts, coerceNumber: true },
    ],
    [catOpts]
  )

  return (
    <EntityCrudPage
      title="Wissensdatenbank"
      resourceBase="/api/v1/knowledge"
      queryKey={['knowledge']}
      columns={columns}
      fields={fields}
    />
  )
}
