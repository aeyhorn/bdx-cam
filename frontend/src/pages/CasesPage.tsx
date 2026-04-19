import { useQuery } from '@tanstack/react-query'
import { DataGrid } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
import { Box, TextField } from '@mui/material'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

type Row = {
  id: number
  ticket_no: string
  title: string
  machine?: { name: string }
  post_processor_version?: { name: string; version: string }
  reporter?: { first_name: string; last_name: string }
  status?: { name: string }
  severity?: { name: string }
  priority?: { name: string }
  assignee?: { first_name: string; last_name: string } | null
  created_at: string
}

export function CasesPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const { data, isLoading, error } = useQuery({
    queryKey: ['cases', search],
    queryFn: async () => (await api.get<Row[]>('/api/v1/cases', { params: { search: search || undefined } })).data,
  })

  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'ticket_no', headerName: 'Ticket', width: 140 },
      { field: 'title', headerName: 'Titel', flex: 1, minWidth: 200 },
      {
        field: 'machine',
        headerName: 'Maschine',
        width: 160,
        valueGetter: (_v, row) => row.machine?.name ?? '',
      },
      {
        field: 'post',
        headerName: 'Post',
        width: 160,
        valueGetter: (_v, row) =>
          row.post_processor_version ? `${row.post_processor_version.name} ${row.post_processor_version.version}` : '',
      },
      {
        field: 'reporter',
        headerName: 'Reporter',
        width: 140,
        valueGetter: (_v, row) => (row.reporter ? `${row.reporter.first_name} ${row.reporter.last_name}` : ''),
      },
      { field: 'status', headerName: 'Status', width: 140, valueGetter: (_v, row) => row.status?.name ?? '' },
      { field: 'severity', headerName: 'Severity', width: 110, valueGetter: (_v, row) => row.severity?.name ?? '' },
      { field: 'priority', headerName: 'Priorität', width: 110, valueGetter: (_v, row) => row.priority?.name ?? '' },
      {
        field: 'assignee',
        headerName: 'Assignee',
        width: 140,
        valueGetter: (_v, row) => (row.assignee ? `${row.assignee.first_name} ${row.assignee.last_name}` : ''),
      },
      { field: 'created_at', headerName: 'Erstellt', width: 180 },
    ],
    []
  )

  return (
    <Box>
      <TextField
        label="Suche"
        size="small"
        sx={{ mb: 2, minWidth: 320 }}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <Box sx={{ height: 560, width: '100%', bgcolor: 'background.paper' }}>
        <DataGrid
          rows={data ?? []}
          columns={columns}
          loading={isLoading}
          onRowClick={(p) => navigate(`/cases/${p.id}`)}
          disableRowSelectionOnClick
        />
      </Box>
      {error && <Box color="error.main">Fehler beim Laden.</Box>}
    </Box>
  )
}
