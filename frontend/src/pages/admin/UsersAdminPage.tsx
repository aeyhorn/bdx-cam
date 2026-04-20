import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { GridColDef } from '@mui/x-data-grid'
import { api } from '../../api/client'
import { EntityCrudPage, type CrudField } from '../../components/crud/EntityCrudPage'

type Role = { id: number; key: string; name: string }

export function UsersAdminPage() {
  const roles = useQuery({
    queryKey: ['roles'],
    queryFn: async () => (await api.get<Role[]>('/api/v1/roles')).data,
  })

  const roleOptions = useMemo(
    () => (roles.data ?? []).map((r) => ({ value: r.id, label: `${r.name} (${r.key})` })),
    [roles.data]
  )

  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'email', headerName: 'E-Mail', flex: 1, minWidth: 180 },
      { field: 'first_name', headerName: 'Vorname', width: 120 },
      { field: 'last_name', headerName: 'Nachname', width: 120 },
      {
        field: 'role',
        headerName: 'Rolle',
        width: 160,
        valueGetter: (_v, row) => (row as { role?: { name: string } }).role?.name ?? '',
      },
      {
        field: 'is_active',
        headerName: 'Aktiv',
        width: 80,
        type: 'boolean',
      },
    ],
    []
  )

  const fields: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'first_name', label: 'Vorname', required: true },
      { kind: 'text', name: 'last_name', label: 'Nachname', required: true },
      { kind: 'email', name: 'email', label: 'E-Mail', required: true },
      {
        kind: 'password',
        name: 'password',
        label: 'Passwort',
        required: true,
        helperCreate: 'Mind. 8 Zeichen',
      },
      {
        kind: 'select',
        name: 'role_id',
        label: 'Rolle',
        required: true,
        options: roleOptions,
        coerceNumber: true,
      },
    ],
    [roleOptions]
  )

  const fieldsEdit: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'first_name', label: 'Vorname', required: true },
      { kind: 'text', name: 'last_name', label: 'Nachname', required: true },
      { kind: 'email', name: 'email', label: 'E-Mail', required: true },
      { kind: 'password', name: 'password', label: 'Neues Passwort (optional)', required: false },
      {
        kind: 'select',
        name: 'role_id',
        label: 'Rolle',
        required: true,
        options: roleOptions,
        coerceNumber: true,
      },
      { kind: 'checkbox', name: 'is_active', label: 'Aktiv' },
    ],
    [roleOptions]
  )

  return (
    <EntityCrudPage
      title="Benutzer"
      resourceBase="/api/v1/users"
      queryKey={['users']}
      columns={columns}
      fields={fields}
      fieldsEdit={fieldsEdit}
      omitEmptyOnEdit={['password']}
    />
  )
}
