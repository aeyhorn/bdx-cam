import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { GridColDef } from '@mui/x-data-grid'
import { api } from '../../api/client'
import { Alert, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material'
import { EntityCrudPage, type CrudField } from '../../components/crud/EntityCrudPage'
import { TextFileEditorDialog } from '../../components/common/TextFileEditorDialog'
import { invalidateAfterEntityWrite } from '../../lib/queryCache'

type Machine = { id: number; name: string }
type CS = { id: number; name: string }
type TestCaseDetail = {
  id: number
  title: string
  description?: string | null
  machine_id?: number | null
  control_system_id?: number | null
  machine?: { id: number; name: string } | null
  control_system?: { id: number; name: string } | null
  scenario_type?: string | null
  expected_result?: string | null
  risk_level?: string | null
  is_active: boolean
  linked_case_ids: number[]
  regression_count: number
  attachments: Array<{
    id: number
    file_name: string
    file_type?: string | null
    attachment_role: string
    linked_project_name?: string | null
    download_url?: string | null
  }>
}

function extractErr(e: unknown): string {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const ax = e as any
  const d = ax?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) {
    return d
      .map((x: unknown) => {
        const m = x as { msg?: string; loc?: unknown[] }
        if (m?.msg && Array.isArray(m?.loc)) return `${m.loc.join('.')}: ${m.msg}`
        if (m?.msg) return m.msg
        try {
          return JSON.stringify(x)
        } catch {
          return String(x)
        }
      })
      .join('; ')
  }
  if (d && typeof d === 'object') {
    try {
      return JSON.stringify(d)
    } catch {
      return String(d)
    }
  }
  return ax?.message ?? 'Import fehlgeschlagen'
}

export function TestCasesPage() {
  const qc = useQueryClient()
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
  const [importOpen, setImportOpen] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [zipFile, setZipFile] = useState<File | null>(null)
  const [importMachine, setImportMachine] = useState('')
  const [importCs, setImportCs] = useState('')
  const [importProject, setImportProject] = useState('')
  const [importReport, setImportReport] = useState<{ created: number; skipped: number; attached_programs: number; errors: string[] } | null>(null)
  const [importError, setImportError] = useState<string | null>(null)
  const [detailId, setDetailId] = useState<number | null>(null)
  const [uploadRole, setUploadRole] = useState<'program' | 'step' | 'other'>('program')
  const [uploadProject, setUploadProject] = useState('')
  const [textOpen, setTextOpen] = useState(false)
  const [textAttId, setTextAttId] = useState<number | null>(null)
  const [textFileName, setTextFileName] = useState('')
  const [textContent, setTextContent] = useState('')

  const importMut = useMutation({
    mutationFn: async () => {
      if (!importFile) throw new Error('Bitte CSV/JSON auswählen')
      const fd = new FormData()
      fd.append('file', importFile)
      if (zipFile) fd.append('programs_zip', zipFile)
      if (importMachine) fd.append('machine_id', importMachine)
      if (importCs) fd.append('control_system_id', importCs)
      if (importProject) fd.append('linked_project_name', importProject)
      const { data } = await api.post('/api/v1/test-cases/import', fd)
      return data as { created: number; skipped: number; attached_programs: number; errors: string[] }
    },
    onSuccess: (r) => {
      setImportError(null)
      setImportReport(r)
      invalidateAfterEntityWrite(qc, '/api/v1/test-cases', ['test-cases'])
    },
    onError: (e: unknown) => setImportError(extractErr(e)),
  })

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
      {
        field: 'control_system',
        headerName: 'Steuerung',
        width: 140,
        valueGetter: (_v, row) => (row as { control_system?: { name: string } }).control_system?.name ?? '',
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

  const detail = useQuery({
    queryKey: ['test-case-detail', detailId],
    enabled: detailId != null,
    queryFn: async () => (await api.get<TestCaseDetail>(`/api/v1/test-cases/${detailId}/detail`)).data,
  })

  const uploadMut = useMutation({
    mutationFn: async (f: File) => {
      if (!detailId) throw new Error('Kein Testfall gewählt')
      const fd = new FormData()
      fd.append('file', f)
      fd.append('attachment_role', uploadRole)
      if (uploadProject) fd.append('linked_project_name', uploadProject)
      await api.post(`/api/v1/test-cases/${detailId}/attachments`, fd)
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['test-case-detail', detailId] })
    },
  })

  const saveTextMut = useMutation({
    mutationFn: async ({ id, content }: { id: number; content: string }) => {
      await api.patch(`/api/v1/test-case-attachments/${id}/text`, { content })
    },
    onSuccess: async () => {
      if (detailId) await qc.invalidateQueries({ queryKey: ['test-case-detail', detailId] })
    },
  })

  const deleteAttMut = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/v1/test-case-attachments/${id}`)
    },
    onSuccess: async () => {
      if (detailId) await qc.invalidateQueries({ queryKey: ['test-case-detail', detailId] })
    },
  })

  async function downloadAttachment(id: number, fileName: string) {
    const resp = await api.get(`/api/v1/test-case-attachments/${id}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(resp.data)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  function classifyAttachment(fileName: string, role: string): string {
    const ext = fileName.split('.').pop()?.toLowerCase() ?? ''
    if (role === 'program') return 'Programm'
    if (ext === 'step' || ext === 'stp') return 'STEP'
    if (ext === 'nc' || ext === 'tap' || ext === 'gcode') return 'NC'
    return 'Datei'
  }

  return (
    <>
      <EntityCrudPage
        title="Testfälle"
        resourceBase="/api/v1/test-cases"
        queryKey={['test-cases']}
        columns={columns}
        fields={fields}
        onRowDoubleClick={(row) => setDetailId(Number(row.id))}
        headerActions={
          <Button variant="outlined" onClick={() => { setImportOpen(true); setImportReport(null); setImportError(null) }}>
            Import (CSV/JSON + ZIP)
          </Button>
        }
      />
      <Dialog open={importOpen} onClose={() => setImportOpen(false)} maxWidth="sm" fullWidth>
      <DialogTitle>Testfälle importieren</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {importError && <Alert severity="error">{importError}</Alert>}
          {importReport && (
            <Alert severity={importReport.errors.length ? 'warning' : 'success'}>
              {`Erstellt: ${importReport.created}, übersprungen: ${importReport.skipped}, Programme zugeordnet: ${importReport.attached_programs}`}
              {importReport.errors.length > 0 && `, Fehler: ${importReport.errors.length}`}
            </Alert>
          )}
          <Button variant="outlined" component="label">
            CSV/JSON wählen
            <input
              hidden
              type="file"
              accept=".json,.csv"
              onChange={(e) => setImportFile(e.target.files?.[0] ?? null)}
            />
          </Button>
          <Button variant="outlined" component="label">
            Programm-ZIP (optional)
            <input
              hidden
              type="file"
              accept=".zip"
              onChange={(e) => setZipFile(e.target.files?.[0] ?? null)}
            />
          </Button>
          <TextField select label="Maschine (optional)" value={importMachine} onChange={(e) => setImportMachine(e.target.value)}>
            {mOpts.map((m) => (
              <MenuItem key={String(m.value)} value={String(m.value)}>
                {m.label}
              </MenuItem>
            ))}
          </TextField>
          <TextField select label="Steuerung (optional)" value={importCs} onChange={(e) => setImportCs(e.target.value)}>
            {csOpts.map((c) => (
              <MenuItem key={String(c.value)} value={String(c.value)}>
                {c.label}
              </MenuItem>
            ))}
          </TextField>
          <TextField label="Projektname (optional)" value={importProject} onChange={(e) => setImportProject(e.target.value)} />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setImportOpen(false)}>Schließen</Button>
        <Button variant="contained" disabled={importMut.isPending || !importFile} onClick={() => importMut.mutate()}>
          Import starten
        </Button>
      </DialogActions>
      </Dialog>

      <Dialog open={detailId != null} onClose={() => setDetailId(null)} maxWidth="lg" fullWidth>
        <DialogTitle>Testfall-Container</DialogTitle>
        <DialogContent>
          {detail.isLoading && <Typography>Lade Testfall...</Typography>}
          {!detail.isLoading && detail.data && (
            <Stack spacing={2} sx={{ pt: 1 }}>
              <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
                <Chip label={`ID ${detail.data.id}`} size="small" />
                <Chip label={detail.data.machine?.name ? `Maschine: ${detail.data.machine.name}` : 'Maschine: —'} size="small" />
                <Chip label={detail.data.control_system?.name ? `Steuerung: ${detail.data.control_system.name}` : 'Steuerung: —'} size="small" />
                <Chip label={`Regressionen: ${detail.data.regression_count}`} size="small" />
                <Chip label={`Change-Bezug: ${detail.data.linked_case_ids.length}`} size="small" />
              </Stack>
              <Typography variant="h6">{detail.data.title}</Typography>
              <Typography variant="body2">{detail.data.description || 'Keine Beschreibung'}</Typography>
              <Typography variant="body2"><b>Erwartung:</b> {detail.data.expected_result || '—'}</Typography>
              <Typography variant="body2"><b>Szenario:</b> {detail.data.scenario_type || '—'} | <b>Risiko:</b> {detail.data.risk_level || '—'}</Typography>
              <Typography variant="subtitle2">Dateien / Programme / STEP</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Datei</TableCell>
                    <TableCell>Klasse</TableCell>
                    <TableCell>Projekt</TableCell>
                    <TableCell align="right">Aktion</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {detail.data.attachments.map((a) => (
                    <TableRow key={a.id}>
                      <TableCell>{a.file_name}</TableCell>
                      <TableCell>{classifyAttachment(a.file_name, a.attachment_role)}</TableCell>
                      <TableCell>{a.linked_project_name || '—'}</TableCell>
                      <TableCell align="right">
                        <Button
                          size="small"
                          onClick={async () => {
                            try {
                              const { data } = await api.get<{ attachment_id: number; file_name: string; content: string }>(`/api/v1/test-case-attachments/${a.id}/text`)
                              setTextAttId(data.attachment_id)
                              setTextFileName(data.file_name)
                              setTextContent(data.content)
                              setTextOpen(true)
                            } catch {
                              await downloadAttachment(a.id, a.file_name)
                            }
                          }}
                        >
                          Anzeigen
                        </Button>
                        <Button size="small" onClick={() => void downloadAttachment(a.id, a.file_name)}>Download</Button>
                        <Button size="small" color="error" disabled={deleteAttMut.isPending} onClick={() => deleteAttMut.mutate(a.id)}>
                          Löschen
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {detail.data.attachments.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4}>Keine Anhänge vorhanden.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
                <TextField select label="Dateityp" size="small" value={uploadRole} onChange={(e) => setUploadRole(e.target.value as 'program' | 'step' | 'other')} sx={{ minWidth: 180 }}>
                  <MenuItem value="program">Programm (NC)</MenuItem>
                  <MenuItem value="step">STEP</MenuItem>
                  <MenuItem value="other">Sonstige</MenuItem>
                </TextField>
                <TextField size="small" label="Projektname (optional)" value={uploadProject} onChange={(e) => setUploadProject(e.target.value)} sx={{ minWidth: 220 }} />
                <Button variant="outlined" component="label" disabled={uploadMut.isPending}>
                  NC/Datei hinzufügen
                  <input
                    hidden
                    type="file"
                    onChange={(e) => {
                      const f = e.target.files?.[0]
                      if (!f) return
                      uploadMut.mutate(f)
                      e.target.value = ''
                    }}
                  />
                </Button>
              </Stack>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <TextField
            select
            label="Dateityp"
            size="small"
            value={uploadRole}
            onChange={(e) => setUploadRole(e.target.value as 'program' | 'step' | 'other')}
            sx={{ minWidth: 170, mr: 1 }}
          >
            <MenuItem value="program">Programm (NC)</MenuItem>
            <MenuItem value="step">STEP</MenuItem>
            <MenuItem value="other">Sonstige</MenuItem>
          </TextField>
          <TextField
            size="small"
            label="Projekt (optional)"
            value={uploadProject}
            onChange={(e) => setUploadProject(e.target.value)}
            sx={{ minWidth: 200, mr: 1 }}
          />
          <Button variant="outlined" component="label" disabled={uploadMut.isPending || detailId == null}>
            Datei hochladen
            <input
              hidden
              type="file"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (!f) return
                uploadMut.mutate(f)
                e.target.value = ''
              }}
            />
          </Button>
          <Button onClick={() => setDetailId(null)}>Schließen</Button>
        </DialogActions>
      </Dialog>

      <TextFileEditorDialog
        open={textOpen}
        title={`Datei-Editor: ${textFileName}`}
        content={textContent}
        onChange={setTextContent}
        onClose={() => setTextOpen(false)}
        onSave={() => textAttId != null && saveTextMut.mutate({ id: textAttId, content: textContent })}
        isSaving={saveTextMut.isPending}
        saveDisabled={textAttId == null}
      />
    </>
  )
}
