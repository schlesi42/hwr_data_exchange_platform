/**
 * Detail-Ansicht einer Anforderung für das Büro.
 * Zeigt alle Zuweisungen und hochgeladene Dateien.
 */
import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import { Download, ArrowLeft } from 'lucide-react'
import { requestsApi } from '@/api/requests'
import { filesApi } from '@/api/files'
import { RequestStatusBadge, AssignmentStatusBadge } from '@/components/StatusBadge'
import { Layout } from '@/components/Layout'
import type { DocumentRequest } from '@/types'

export default function RequestDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [request, setRequest] = useState<DocumentRequest | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (id) {
      requestsApi
        .get(parseInt(id))
        .then(setRequest)
        .finally(() => setIsLoading(false))
    }
  }, [id])

  async function handleDownload(fileId: number, filename: string) {
    const file = await filesApi.getDownloadUrl(fileId)
    if (file.download_url) {
      const a = document.createElement('a')
      a.href = file.download_url
      a.download = filename
      a.click()
    }
  }

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
        </div>
      </Layout>
    )
  }

  if (!request) {
    return (
      <Layout>
        <p className="text-gray-500">Anforderung nicht gefunden.</p>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Zurück-Link */}
        <Link to="/buero" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
          <ArrowLeft size={16} /> Zurück zur Übersicht
        </Link>

        {/* Header */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{request.title}</h1>
              {request.description && (
                <p className="text-gray-600 mt-2">{request.description}</p>
              )}
            </div>
            <RequestStatusBadge status={request.status} />
          </div>

          <div className="flex gap-6 mt-4 text-sm text-gray-600">
            <span>
              <strong>Deadline:</strong>{' '}
              {format(new Date(request.deadline), 'dd. MMMM yyyy', { locale: de })}
            </span>
            <span>
              <strong>Erstellt:</strong>{' '}
              {format(new Date(request.created_at), 'dd.MM.yyyy', { locale: de })}
            </span>
            <span>
              <strong>Fortschritt:</strong>{' '}
              {request.assignments.filter((a) => a.status === 'uploaded').length} /{' '}
              {request.assignments.length} eingereicht
            </span>
          </div>
        </div>

        {/* Zuweisungen */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Dozierende</h2>
          {request.assignments.map((assignment) => (
            <div
              key={assignment.id}
              className="bg-white rounded-xl border border-gray-200 p-5"
            >
              <div className="flex justify-between items-start mb-3">
                <div>
                  <p className="font-medium text-gray-900">
                    {assignment.dozent_name || assignment.dozent_email}
                  </p>
                  <p className="text-sm text-gray-500">{assignment.dozent_email}</p>
                </div>
                <AssignmentStatusBadge status={assignment.status} />
              </div>

              {assignment.submitted_at && (
                <p className="text-xs text-gray-400 mb-3">
                  Eingereicht am:{' '}
                  {format(new Date(assignment.submitted_at), 'dd.MM.yyyy HH:mm', { locale: de })}
                </p>
              )}

              {/* Hochgeladene Dateien */}
              {assignment.files.length > 0 ? (
                <div className="space-y-1">
                  {assignment.files.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                    >
                      <span className="text-sm text-gray-700">{file.filename}</span>
                      <button
                        onClick={() => handleDownload(file.id, file.filename)}
                        className="flex items-center gap-1 text-primary-600 hover:underline text-sm"
                      >
                        <Download size={14} /> Herunterladen
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400 italic">Noch keine Dateien hochgeladen.</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </Layout>
  )
}
