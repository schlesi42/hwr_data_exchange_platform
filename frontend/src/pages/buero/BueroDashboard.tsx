/**
 * Büro-Dashboard – Hauptseite für Fachbereichsbüros.
 *
 * Zeigt:
 *   - Übersicht aller Anforderungen mit Status
 *   - Schnellzugriff zum Erstellen neuer Anforderungen
 *   - Deadline-Ampel (rot = überfällig, gelb = bald fällig)
 */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Clock, CheckCircle, AlertCircle } from 'lucide-react'
import { format, isPast, differenceInDays } from 'date-fns'
import { de } from 'date-fns/locale'
import { requestsApi } from '@/api/requests'
import { RequestStatusBadge } from '@/components/StatusBadge'
import { Layout } from '@/components/Layout'
import type { DocumentRequestSummary } from '@/types'

export default function BueroDashboard() {
  const [requests, setRequests] = useState<DocumentRequestSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    requestsApi
      .list()
      .then(setRequests)
      .catch(() => setError('Fehler beim Laden der Anforderungen.'))
      .finally(() => setIsLoading(false))
  }, [])

  // Statistiken für die Kacheln oben
  const stats = {
    total: requests.length,
    open: requests.filter((r) => r.status === 'open' || r.status === 'partial').length,
    completed: requests.filter((r) => r.status === 'completed').length,
    overdue: requests.filter((r) => r.status === 'overdue').length,
  }

  function getDeadlineColor(deadline: string): string {
    const date = new Date(deadline)
    const daysLeft = differenceInDays(date, new Date())
    if (isPast(date)) return 'text-red-600 font-semibold'
    if (daysLeft <= 3) return 'text-orange-500 font-medium'
    if (daysLeft <= 7) return 'text-yellow-600'
    return 'text-gray-600'
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

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Meine Anforderungen</h1>
          <Link
            to="/buero/requests/new"
            className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Plus size={18} />
            Neue Anforderung
          </Link>
        </div>

        {/* Statistik-Kacheln */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard icon={<Clock className="text-blue-500" />} label="Gesamt" value={stats.total} />
          <StatCard icon={<AlertCircle className="text-yellow-500" />} label="Offen" value={stats.open} />
          <StatCard icon={<CheckCircle className="text-green-500" />} label="Vollständig" value={stats.completed} />
          <StatCard
            icon={<AlertCircle className="text-red-500" />}
            label="Überfällig"
            value={stats.overdue}
            highlight={stats.overdue > 0}
          />
        </div>

        {/* Fehler */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>
        )}

        {/* Anforderungs-Tabelle */}
        {requests.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
            <p className="text-gray-500 text-lg">Noch keine Anforderungen vorhanden.</p>
            <Link
              to="/buero/requests/new"
              className="mt-4 inline-flex items-center gap-2 text-primary-600 hover:underline"
            >
              <Plus size={16} /> Erste Anforderung erstellen
            </Link>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Titel</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Deadline</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Fortschritt</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Status</th>
                  <th className="py-3 px-4"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {requests.map((req) => (
                  <tr key={req.id} className="hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 font-medium text-gray-900">{req.title}</td>
                    <td className={`py-3 px-4 ${getDeadlineColor(req.deadline)}`}>
                      {format(new Date(req.deadline), 'dd.MM.yyyy', { locale: de })}
                    </td>
                    <td className="py-3 px-4 text-gray-600">
                      {req.uploaded_count} / {req.total_assignments}
                    </td>
                    <td className="py-3 px-4">
                      <RequestStatusBadge status={req.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/buero/requests/${req.id}`}
                        className="text-primary-600 hover:underline text-sm"
                      >
                        Details →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  )
}

function StatCard({
  icon,
  label,
  value,
  highlight = false,
}: {
  icon: React.ReactNode
  label: string
  value: number
  highlight?: boolean
}) {
  return (
    <div
      className={`bg-white rounded-xl p-4 border ${
        highlight ? 'border-red-300 bg-red-50' : 'border-gray-200'
      }`}
    >
      <div className="flex items-center gap-2 mb-1">{icon}<span className="text-sm text-gray-600">{label}</span></div>
      <div className={`text-3xl font-bold ${highlight ? 'text-red-600' : 'text-gray-900'}`}>
        {value}
      </div>
    </div>
  )
}
