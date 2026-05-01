/**
 * Dozenten-Dashboard – Übersicht aller offenen Aufgaben.
 */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { format, isPast, differenceInDays } from 'date-fns'
import { de } from 'date-fns/locale'
import { Upload, CheckCircle } from 'lucide-react'
import { requestsApi } from '@/api/requests'
import { AssignmentStatusBadge } from '@/components/StatusBadge'
import { Layout } from '@/components/Layout'
import { useAuth } from '@/auth/AuthContext'
import type { DocumentRequestSummary } from '@/types'

export default function DozentDashboard() {
  const { user } = useAuth()
  const [requests, setRequests] = useState<DocumentRequestSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    requestsApi.list().then(setRequests).finally(() => setIsLoading(false))
  }, [])

  function getDeadlineText(deadline: string): { text: string; className: string } {
    const date = new Date(deadline)
    const daysLeft = differenceInDays(date, new Date())
    if (isPast(date)) return { text: 'Überfällig!', className: 'text-red-600 font-bold' }
    if (daysLeft === 0) return { text: 'Heute fällig!', className: 'text-red-500 font-semibold' }
    if (daysLeft === 1) return { text: 'Morgen fällig', className: 'text-orange-500 font-medium' }
    if (daysLeft <= 7) return { text: `Noch ${daysLeft} Tage`, className: 'text-yellow-600' }
    return {
      text: format(date, 'dd.MM.yyyy', { locale: de }),
      className: 'text-gray-600',
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

  const pending = requests.filter((r) => r.status !== 'completed')
  const completed = requests.filter((r) => r.status === 'completed')

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Meine Aufgaben</h1>
          <p className="text-gray-500 mt-1">Willkommen, {user?.name || user?.email}</p>
        </div>

        {/* Offene Aufgaben */}
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            Ausstehende Anforderungen ({pending.length})
          </h2>
          {pending.length === 0 ? (
            <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
              <CheckCircle className="text-green-500 mx-auto mb-2" size={32} />
              <p className="text-green-700 font-medium">Alles erledigt! Keine offenen Aufgaben.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {pending.map((req) => {
                const deadline = getDeadlineText(req.deadline)
                return (
                  <div
                    key={req.id}
                    className="bg-white rounded-xl border border-gray-200 p-5 flex justify-between items-center"
                  >
                    <div>
                      <h3 className="font-medium text-gray-900">{req.title}</h3>
                      <p className="text-sm mt-1">
                        <span className="text-gray-500">Deadline: </span>
                        <span className={deadline.className}>{deadline.text}</span>
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">{req.department_name}</p>
                    </div>
                    <Link
                      to={`/dozent/upload/${req.id}`}
                      className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors text-sm"
                    >
                      <Upload size={16} />
                      Dokument hochladen
                    </Link>
                  </div>
                )
              })}
            </div>
          )}
        </section>

        {/* Erledigte Aufgaben */}
        {completed.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Eingereichte Anforderungen ({completed.length})
            </h2>
            <div className="space-y-2">
              {completed.map((req) => (
                <div
                  key={req.id}
                  className="bg-gray-50 rounded-xl border border-gray-200 p-4 flex justify-between items-center opacity-75"
                >
                  <div>
                    <h3 className="font-medium text-gray-700">{req.title}</h3>
                    <p className="text-xs text-gray-400">{req.department_name}</p>
                  </div>
                  <AssignmentStatusBadge status="uploaded" />
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </Layout>
  )
}
