/**
 * Upload-Seite für Dozierende.
 *
 * Ablauf:
 *   1. Anforderungsdetails anzeigen
 *   2. Datei auswählen
 *   3. Upload-URL vom Backend anfordern
 *   4. Direkt zu S3 hochladen (mit Fortschrittsbalken)
 *   5. Upload bestätigen
 */
import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useRef } from 'react'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import { Upload, FileText, CheckCircle } from 'lucide-react'
import { requestsApi } from '@/api/requests'
import { filesApi } from '@/api/files'
import { useAuth } from '@/auth/AuthContext'
import { Layout } from '@/components/Layout'
import type { DocumentRequest, Assignment } from '@/types'

const ALLOWED_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]

const TYPE_LABELS: Record<string, string> = {
  'application/pdf': 'PDF',
  'application/msword': 'Word (.doc)',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word (.docx)',
}

export default function UploadPage() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuth()
  const navigate = useNavigate()

  const [request, setRequest] = useState<DocumentRequest | null>(null)
  const [myAssignment, setMyAssignment] = useState<Assignment | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadDone, setUploadDone] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (id) {
      requestsApi.get(parseInt(id)).then((req) => {
        setRequest(req)
        const assignment = req.assignments.find((a) => a.dozent_id === user?.id)
        setMyAssignment(assignment || null)
      })
    }
  }, [id, user])

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    if (!ALLOWED_TYPES.includes(file.type)) {
      setError('Nur PDF und Word-Dokumente sind erlaubt.')
      return
    }

    if (file.size > 100 * 1024 * 1024) {
      setError('Datei ist zu groß (max. 100 MB).')
      return
    }

    setError(null)
    setSelectedFile(file)
  }

  async function handleUpload() {
    if (!selectedFile || !myAssignment) return

    setIsUploading(true)
    setError(null)

    try {
      // 1. Upload-URL anfordern
      const { upload_url, s3_key } = await filesApi.getUploadUrl({
        assignment_id: myAssignment.id,
        filename: selectedFile.name,
        content_type: selectedFile.type,
        size_bytes: selectedFile.size,
      })

      // 2. Direkt zu S3 hochladen
      await filesApi.uploadToS3(upload_url, selectedFile, setUploadProgress)

      // 3. Upload bestätigen
      await filesApi.confirmUpload({
        assignment_id: myAssignment.id,
        s3_key,
        filename: selectedFile.name,
        content_type: selectedFile.type,
        size_bytes: selectedFile.size,
      })

      setUploadDone(true)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload fehlgeschlagen.'
      setError(msg)
    } finally {
      setIsUploading(false)
    }
  }

  if (!request) {
    return (
      <Layout>
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
        </div>
      </Layout>
    )
  }

  if (uploadDone) {
    return (
      <Layout>
        <div className="max-w-xl mx-auto text-center py-16">
          <CheckCircle className="text-green-500 mx-auto mb-4" size={48} />
          <h2 className="text-2xl font-bold text-gray-900">Erfolgreich hochgeladen!</h2>
          <p className="text-gray-600 mt-2">
            Ihre Dokumente wurden erfolgreich eingereicht.
          </p>
          <button
            onClick={() => navigate('/dozent')}
            className="mt-6 bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors"
          >
            Zurück zur Übersicht
          </button>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Anforderungsdetails */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{request.title}</h1>
          {request.description && <p className="text-gray-600">{request.description}</p>}
          <p className="text-sm text-gray-500 mt-3">
            <strong>Deadline:</strong>{' '}
            {format(new Date(request.deadline), 'dd. MMMM yyyy', { locale: de })}
          </p>
        </div>

        {/* Bereits hochgeladene Dateien */}
        {myAssignment && myAssignment.files.length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <h3 className="font-medium text-green-800 mb-2">Bereits hochgeladene Dokumente:</h3>
            {myAssignment.files.map((file) => (
              <div key={file.id} className="flex items-center gap-2 text-sm text-green-700">
                <FileText size={14} />
                {file.filename}
              </div>
            ))}
          </div>
        )}

        {/* Upload-Bereich */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Dokument hochladen</h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Dateiauswahl */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              selectedFile
                ? 'border-primary-400 bg-primary-50'
                : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Upload className="mx-auto text-gray-400 mb-2" size={32} />
            {selectedFile ? (
              <div>
                <p className="font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {TYPE_LABELS[selectedFile.type]} –{' '}
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            ) : (
              <div>
                <p className="text-gray-600">Klicken Sie hier oder ziehen Sie eine Datei hierher</p>
                <p className="text-xs text-gray-400 mt-1">PDF oder Word, max. 100 MB</p>
              </div>
            )}
          </div>

          {/* Fortschrittsbalken */}
          {isUploading && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Wird hochgeladen...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Upload-Button */}
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            className="mt-4 w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors font-medium"
          >
            {isUploading ? `Hochladen... ${uploadProgress}%` : 'Dokument einreichen'}
          </button>
        </div>
      </div>
    </Layout>
  )
}
