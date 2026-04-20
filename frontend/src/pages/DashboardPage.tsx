import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import Grid from '@mui/material/Grid'
import { Chip, Paper, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

type BuildStatus = {
  component: string
  latest_build_no: number
  latest_version_label: string
  latest_created_at: string
  deployed_build_no: number | null
  deployed_version_label: string | null
  deployed_created_at: string | null
  is_outdated: boolean
}

export function DashboardPage() {
  const { user } = useAuth()
  const role = user?.role.key

  const prod = useQuery({
    queryKey: ['dash', 'prod'],
    enabled: role === 'FEEDBACK_PRODUCTION',
    queryFn: async () => (await api.get('/api/v1/dashboard/production')).data,
  })
  const eng = useQuery({
    queryKey: ['dash', 'eng'],
    enabled: role === 'ENGINEERING',
    queryFn: async () => (await api.get('/api/v1/dashboard/engineering')).data,
  })
  const adm = useQuery({
    queryKey: ['dash', 'adm'],
    enabled: role === 'ADMIN',
    queryFn: async () => (await api.get('/api/v1/dashboard/admin')).data,
  })

  if (role === 'ADMIN') {
    const d = adm.data
    const builds = (d?.system_builds ?? []) as BuildStatus[]
    return (
      <Grid container spacing={2}>
        <Tile title="Aktive Nutzer" value={d?.active_users} />
        <Tile title="Offene Fälle" value={d?.open_cases} />
        <Grid size={{ xs: 12 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2">Häufigste Fehlerkategorien</Typography>
            <pre style={{ margin: 0, fontSize: 12 }}>{JSON.stringify(d?.top_error_categories, null, 2)}</pre>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2">Produktive Post-Versionen</Typography>
            <pre style={{ margin: 0, fontSize: 12 }}>{JSON.stringify(d?.productive_post_versions, null, 2)}</pre>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12 }}>
          <BuildStatusPanel builds={builds} />
        </Grid>
      </Grid>
    )
  }

  if (role === 'ENGINEERING') {
    const d = eng.data
    const builds = (d?.system_builds ?? []) as BuildStatus[]
    return (
      <Grid container spacing={2}>
        <Tile title="Neue Fälle" value={d?.new_cases} />
        <Tile title="Kritisch" value={d?.critical_cases} />
        <Tile title="Unzugewiesen" value={d?.unassigned_cases} />
        <Tile title="Ohne Root Cause" value={d?.cases_without_root_cause} />
        <Tile title="In Test" value={d?.cases_in_test} />
        <Tile title="Offene Regressionen" value={d?.open_regressions} />
        <Grid size={{ xs: 12 }}>
          <BuildStatusPanel builds={builds} />
        </Grid>
      </Grid>
    )
  }

  const d = prod.data
  const builds = (d?.system_builds ?? []) as BuildStatus[]
  return (
    <Grid container spacing={2}>
      <Tile title="Meine offenen Fälle" value={d?.my_open_cases} />
      <Tile title="Offene Rückfragen" value={d?.open_questions} />
      <Grid size={{ xs: 12 }}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2">Letzte Meldungen</Typography>
          <pre style={{ margin: 0, fontSize: 12 }}>{JSON.stringify(d?.recent_cases, null, 2)}</pre>
        </Paper>
      </Grid>
      <Grid size={{ xs: 12 }}>
        <BuildStatusPanel builds={builds} />
      </Grid>
    </Grid>
  )
}

function Tile({ title, value }: { title: string; value?: number }) {
  return (
    <Grid size={{ xs: 12, sm: 6, md: 4 }}>
      <Paper sx={{ p: 2 }}>
        <Typography variant="caption" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h4">{value ?? '—'}</Typography>
      </Paper>
    </Grid>
  )
}

function BuildStatusPanel({ builds }: { builds: BuildStatus[] }) {
  const rows = useMemo(() => builds.slice().sort((a, b) => a.component.localeCompare(b.component)), [builds])
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        System-Build-Versionen
      </Typography>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5 }}>
        Vergleich zwischen zuletzt erstellt und aktuell im Einsatz. Markierung zeigt, ob der Bereich veraltet ist.
      </Typography>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Softwareteil</TableCell>
            <TableCell>Im Einsatz</TableCell>
            <TableCell>Letzter Build</TableCell>
            <TableCell align="right">Status</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4}>Keine Build-Versionen gepflegt.</TableCell>
            </TableRow>
          ) : (
            rows.map((r) => (
              <TableRow key={r.component}>
                <TableCell>{r.component}</TableCell>
                <TableCell>
                  {r.deployed_build_no != null ? `#${r.deployed_build_no} · ${r.deployed_version_label ?? '—'}` : '—'}
                </TableCell>
                <TableCell>{`#${r.latest_build_no} · ${r.latest_version_label}`}</TableCell>
                <TableCell align="right">
                  <Chip
                    size="small"
                    label={r.is_outdated ? 'Veraltet' : 'Aktuell'}
                    color={r.is_outdated ? 'warning' : 'success'}
                    variant={r.is_outdated ? 'filled' : 'outlined'}
                  />
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Paper>
  )
}
