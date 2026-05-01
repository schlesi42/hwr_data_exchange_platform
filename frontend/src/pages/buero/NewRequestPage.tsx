/**
 * Neue Anforderung erstellen.
 *
 * Formular mit:
 *   - Titel und Beschreibung
 *   - Deadline (Datepicker)
 *   - Dozenten-Auswahl (Checkboxen)
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { format } from 'date-fns'
import { requestsApi } from '@/api/requests'
import { usersApi } from '@/api/users'
import { Layout } from '@/components/Layout'
import type { User } from '@/types'

interface RequestForm {
  title: string
  description: string
  deadline: string
  dozent_ids: number[]
}

export default function NewRequestPage() {
  const navigate = useNavigate()
  const [dozents, setDozents] = useState<User[]>([])
  const [selectedDozentIds, setSelectedDozentIds] = useState<number[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { register, handleSubmit, formState: { errors } } = useForm<RequestForm>()

  useEffect(() => {
    usersApi.list({ role: 'dozent' }).then(setDozents)
  }, [])

  function toggleDozent(id: number) {
    setSelectedDozentIds((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    )
  }

  async function onSubmit(data: RequestForm) {
    if (selectedDozentIds.length === 0) {
      setError('Bitte wählen Sie mindestens einen Dozenten aus.')
      return
    }

    setIsLoading(true)
    setError(null)
    try {
      const req = await requestsApi.create({
        title: data.title,
        description: data.description || undefined,
        deadline: new Date(data.deadline).toISOString(),
        dozent_ids: selectedDozentIds,
      })
      navigate(`/buero/requests/${req.id}`)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Fehler beim Erstellen.'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  // Minimum-Datum: morgen
  const tomorrow = format(new Date(Date.now() + 86400000), "yyyy-MM-dd")

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Neue Anforderung erstellen</h1>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 bg-white rounded-xl border border-gray-200 p-6">
          {/* Titel */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Titel *</label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="z.B. Lehrveranstaltungsnachweise WS 2024/25"
              {...register('title', { required: 'Titel ist erforderlich.' })}
            />
            {errors.title && <p className="text-red-500 text-xs mt-1">{errors.title.message}</p>}
          </div>

          {/* Beschreibung */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Beschreibung <span className="text-gray-400">(optional)</span>
            </label>
            <textarea
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Welche Dokumente werden benötigt? Besondere Hinweise?"
              {...register('description')}
            />
          </div>

          {/* Deadline */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Deadline *</label>
            <input
              type="date"
              min={tomorrow}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              {...register('deadline', { required: 'Deadline ist erforderlich.' })}
            />
            {errors.deadline && <p className="text-red-500 text-xs mt-1">{errors.deadline.message}</p>}
          </div>

          {/* Dozenten-Auswahl */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dozierende auswählen *
            </label>
            {dozents.length === 0 ? (
              <p className="text-gray-500 text-sm">
                Keine Dozierenden in Ihrem Fachbereich gefunden.
                Bitte legen Sie zuerst Dozierende an.
              </p>
            ) : (
              <div className="border border-gray-200 rounded-lg divide-y divide-gray-100 max-h-64 overflow-y-auto">
                {dozents.map((d) => (
                  <label
                    key={d.id}
                    className="flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedDozentIds.includes(d.id)}
                      onChange={() => toggleDozent(d.id)}
                      className="rounded border-gray-300 text-primary-600"
                    />
                    <span className="text-sm">
                      {d.name ? `${d.name} (${d.email})` : d.email}
                    </span>
                  </label>
                ))}
              </div>
            )}
            <p className="text-xs text-gray-500 mt-1">
              {selectedDozentIds.length} von {dozents.length} ausgewählt
            </p>
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors font-medium"
            >
              {isLoading ? 'Wird erstellt...' : 'Anforderung erstellen & E-Mails versenden'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/buero')}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Abbrechen
            </button>
          </div>
        </form>
      </div>
    </Layout>
  )
}
