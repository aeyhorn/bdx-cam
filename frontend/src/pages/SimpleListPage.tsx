import { useQuery } from '@tanstack/react-query'
import { DataGrid } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
import { Box, Typography } from '@mui/material'
import { api } from '../api/client'
import { useMemo } from 'react'

export function SimpleListPage({ title, url }: { title: string; url: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['list', url],
    queryFn: async () => (await api.get(url)).data as Record<string, unknown>[],
  })

  const columns: GridColDef[] = useMemo(() => {
    const row = (data && data[0]) || {}
    return Object.keys(row).map((k) => ({ field: k, headerName: k, flex: 1, minWidth: 120 }))
  }, [data])

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <Box sx={{ height: 520, width: '100%', bgcolor: 'background.paper' }}>
        <DataGrid rows={(data as { id: number }[]) ?? []} columns={columns} loading={isLoading} getRowId={(r) => r.id} />
      </Box>
      {error && <Typography color="error">Fehler</Typography>}
    </Box>
  )
}
