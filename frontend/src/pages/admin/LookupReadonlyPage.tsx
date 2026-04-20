import { useQuery } from '@tanstack/react-query'
import { Box, Typography } from '@mui/material'
import { DataGrid, type GridColDef } from '@mui/x-data-grid'
import { useMemo } from 'react'
import { api } from '../../api/client'

export function SeveritiesListPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['severities'],
    queryFn: async () => (await api.get<Record<string, unknown>[]>('/api/v1/severities')).data,
  })
  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'key', headerName: 'Schlüssel', width: 140 },
      { field: 'name', headerName: 'Name', flex: 1 },
      { field: 'sort_order', headerName: 'Sort', width: 90 },
    ],
    []
  )
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Severity
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Stammdaten nur lesen (Änderungen über Admin-DB / zukünftige API).
      </Typography>
      <Box sx={{ height: '65vh', minHeight: 420, bgcolor: 'background.paper' }}>
        <DataGrid rows={(data as { id: number }[]) ?? []} columns={columns} loading={isLoading} getRowId={(r) => r.id} density="compact" rowHeight={34} columnHeaderHeight={36} disableRowSelectionOnClick sx={{ fontSize: 12 }} />
      </Box>
    </Box>
  )
}

export function PrioritiesListPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['priorities'],
    queryFn: async () => (await api.get<Record<string, unknown>[]>('/api/v1/priorities')).data,
  })
  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'key', headerName: 'Schlüssel', width: 140 },
      { field: 'name', headerName: 'Name', flex: 1 },
      { field: 'sort_order', headerName: 'Sort', width: 90 },
    ],
    []
  )
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Priorität
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Stammdaten nur lesen.
      </Typography>
      <Box sx={{ height: '65vh', minHeight: 420, bgcolor: 'background.paper' }}>
        <DataGrid rows={(data as { id: number }[]) ?? []} columns={columns} loading={isLoading} getRowId={(r) => r.id} density="compact" rowHeight={34} columnHeaderHeight={36} disableRowSelectionOnClick sx={{ fontSize: 12 }} />
      </Box>
    </Box>
  )
}
