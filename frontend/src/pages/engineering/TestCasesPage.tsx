import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { GridColDef } from '@mui/x-data-grid'
import { api } from '../../api/client'
import { EntityCrudPage, type CrudField } from '../../components/crud/EntityCrudPage'

type Machine = { id: number; name: string }
type CS = { id: number; name: string }

export function TestCasesPage() {
  const machines = useQuery({
    queryKey: ['machines'],
    queryFn: async () => (await api.get<Machine[]>('/api/v1/machines')).data,
  })
  const csList = useQuery({
    queryKey: ['control-systems'],
    queryFn: async () => (await api.get<CS[]>('/api/v1/control-systems')).data,
  })

  const mOpts = useMemo(
    () => [{ value: '', label: '—' }, ...(machines.data ?? []).map((m) => ({ value: m.id, label: m.name }))],
    [machines.data]
  )
  const csOpts = useMemo(
    () => [{ value: '', label: '—' }, ...(csList.data ?? []).map((c) => ({ value: c.id, label: c.name }))],
    [csList.data]
  )

  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'title', headerName: 'Titel', flex: 1, minWidth: 200 },
      {
        field: 'machine',
        headerName: 'Maschine',
        width: 140,
        valueGetter: (_v, row) => (row as { machine?: { name: string } }).machine?.name ?? '',
      },
      { field: 'scenario_type', headerName: 'Szenario', width: 120 },
      { field: 'is_active', headerName: 'Aktiv', width: 80, type: 'boolean' },
    ],
    []
  )

  const fields: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'title', label: 'Titel', required: true },
      { kind: 'text', name: 'description', label: 'Beschreibung', multiline: true, rows: 3 },
      { kind: 'select', name: 'machine_id', label: 'Maschine', required: false, options: mOpts, coerceNumber: true },
      { kind: 'select', name: 'control_system_id', label: 'Steuerung', required: false, options: csOpts, coerceNumber: true },
      { kind: 'text', name: 'scenario_type', label: 'Szenario-Typ' },
      { kind: 'text', name: 'expected_result', label: 'Erwartetes Ergebnis', multiline: true, rows: 2 },
      { kind: 'text', name: 'risk_level', label: 'Risiko' },
      { kind: 'checkbox', name: 'is_active', label: 'Aktiv' },
    ],
    [mOpts, csOpts]
  )

  return (
    <EntityCrudPage
      title="Testfälle"
      resourceBase="/api/v1/test-cases"
      queryKey={['test-cases']}
      columns={columns}
      fields={fields}
    />
  )
}
