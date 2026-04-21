import { useMemo, useState } from 'react'
import type { GridColDef } from '@mui/x-data-grid'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, Typography } from '@mui/material'
import { api } from '../../api/client'
import { EntityCrudPage, type CrudField } from '../../components/crud/EntityCrudPage'
import { TextFileEditorDialog } from '../../components/common/TextFileEditorDialog'

const statusOpts = [
  { value: 'draft', label: 'Entwurf' },
  { value: 'released', label: 'Released' },
  { value: 'deprecated', label: 'Deprecated' },
]

export function PostVersionsAdminPage() {
  const qc = useQueryClient()
  const [codeOpen, setCodeOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [selectedName, setSelectedName] = useState('')
  const [codeFileName, setCodeFileName] = useState<string | null>(null)
  const [textOpen, setTextOpen] = useState(false)
  const [textContent, setTextContent] = useState('')
  const [msg, setMsg] = useState<string | null>(null)

  const refresh = async () => {
    await qc.invalidateQueries({ queryKey: ['post-versions'] })
  }

  const uploadCodeMut = useMutation({
    mutationFn: async (f: File) => {
      if (!selectedId) throw new Error('Keine Post-Version gewählt')
      const fd = new FormData()
      fd.append('file', f)
      const { data } = await api.post<{ code_file_name?: string | null }>(`/api/v1/post-versions/${selectedId}/code`, fd)
      return data
    },
    onSuccess: async (d) => {
      setCodeFileName(d.code_file_name ?? null)
      await refresh()
    },
  })

  const deleteCodeMut = useMutation({
    mutationFn: async () => {
      if (!selectedId) throw new Error('Keine Post-Version gewählt')
      const { data } = await api.delete<{ code_file_name?: string | null }>(`/api/v1/post-versions/${selectedId}/code`)
      return data
    },
    onSuccess: async () => {
      setCodeFileName(null)
      await refresh()
    },
  })

  const saveTextMut = useMutation({
    mutationFn: async () => {
      if (!selectedId) throw new Error('Keine Post-Version gewählt')
      await api.patch(`/api/v1/post-versions/${selectedId}/code/text`, { content: textContent })
    },
    onSuccess: async () => {
      await refresh()
    },
  })

  async function downloadCode() {
    if (!selectedId) return
    const response = await api.get(`/api/v1/post-versions/${selectedId}/code`, { responseType: 'blob' })
    const fileName = codeFileName || `${selectedName || 'post-code'}.txt`
    const url = URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  async function openTextEditor() {
    if (!selectedId) return
    try {
      const { data } = await api.get<{ content: string }>(`/api/v1/post-versions/${selectedId}/code/text`)
      setTextContent(data.content)
      setTextOpen(true)
      setMsg(null)
    } catch {
      await downloadCode()
      setMsg('Datei ist nicht als Text lesbar. Download wurde gestartet.')
    }
  }

  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'name', headerName: 'Name', width: 160 },
      { field: 'version', headerName: 'Version', width: 100 },
      { field: 'machine_family', headerName: 'Familie', width: 140 },
      { field: 'status', headerName: 'Status', width: 110 },
      { field: 'code_file_name', headerName: 'Code-Anhang', width: 220, valueGetter: (_v, row) => (row as { code_file_name?: string | null }).code_file_name || '—' },
      { field: 'is_productive', headerName: 'Produktiv', width: 100, type: 'boolean' },
    ],
    []
  )

  const fields: CrudField[] = useMemo(
    () => [
      { kind: 'text', name: 'name', label: 'Name', required: true },
      { kind: 'text', name: 'version', label: 'Version', required: true },
      { kind: 'text', name: 'machine_family', label: 'Maschinenfamilie', required: true },
      { kind: 'text', name: 'description', label: 'Beschreibung', multiline: true, rows: 2 },
      { kind: 'select', name: 'status', label: 'Status', required: true, options: statusOpts },
      { kind: 'checkbox', name: 'is_productive', label: 'Produktiv freigegeben' },
      { kind: 'date', name: 'release_date', label: 'Release-Datum' },
      { kind: 'text', name: 'notes', label: 'Notizen', multiline: true, rows: 2 },
    ],
    []
  )

  return (
    <>
      <EntityCrudPage
        title="Post-Versionen"
        resourceBase="/api/v1/post-versions"
        queryKey={['post-versions']}
        columns={columns}
        fields={fields}
        onRowDoubleClick={(row) => {
          setSelectedId(Number(row.id))
          setSelectedName(String(row.name ?? ''))
          setCodeFileName((row.code_file_name as string | null | undefined) ?? null)
          setCodeOpen(true)
        }}
      />
      <Dialog open={codeOpen} onClose={() => setCodeOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Post-Code-Anhang</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            {msg && <Alert severity="info">{msg}</Alert>}
            <Typography variant="body2">{selectedName ? `Post: ${selectedName}` : 'Post-Version'}</Typography>
            <Typography variant="body2">{`Aktueller Anhang: ${codeFileName ?? 'kein Code hinterlegt'}`}</Typography>
            <Button variant="outlined" component="label" disabled={uploadCodeMut.isPending || selectedId == null}>
              Code-Datei hochladen
              <input
                hidden
                type="file"
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (!f) return
                  uploadCodeMut.mutate(f)
                  e.target.value = ''
                }}
              />
            </Button>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => void openTextEditor()} disabled={!codeFileName}>
            Anzeigen
          </Button>
          <Button onClick={() => void downloadCode()} disabled={!codeFileName}>Download</Button>
          <Button color="error" onClick={() => deleteCodeMut.mutate()} disabled={!codeFileName || deleteCodeMut.isPending}>Löschen</Button>
          <Button onClick={() => setCodeOpen(false)}>Schließen</Button>
        </DialogActions>
      </Dialog>
      <TextFileEditorDialog
        open={textOpen}
        title={`Post-Code-Editor: ${codeFileName ?? selectedName}`}
        content={textContent}
        onChange={setTextContent}
        onClose={() => setTextOpen(false)}
        onSave={() => void saveTextMut.mutate()}
        isSaving={saveTextMut.isPending}
        saveDisabled={!codeFileName}
      />
    </>
  )
}
