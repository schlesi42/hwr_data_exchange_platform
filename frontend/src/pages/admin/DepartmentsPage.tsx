/**
 * Fachbereiche verwalten (Admin).
 */
import { useEffect, useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { departmentsApi } from '@/api/departments'
import { Layout } from '@/components/Layout'
import type { Department } from '@/types'

interface DepartmentForm {
  name: string
  slug: string
}

export default function DepartmentsPage() {
  const [departments, setDepartments] = useState<Department[]>([])
  const [isAdding, setIsAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm<DepartmentForm>()

  // Slug automatisch aus Name generieren
  const nameValue = watch('name', '')
  useEffect(() => {
    const slug = nameValue
      .toLowerCase()
      .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
    setValue('slug', slug)
  }, [nameValue, setValue])

  useEffect(() => {
    departmentsApi.list().then(setDepartments)
  }, [])

  async function onSubmit(data: DepartmentForm) {
    try {
      const dept = await departmentsApi.create(data)
      setDepartments((prev) => [...prev, dept])
      reset()
      setIsAdding(false)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Fehler beim Erstellen.'
      setError(msg)
    }
  }

  async function handleDelete(id: number, name: string) {
    if (!confirm(`Fachbereich "${name}" wirklich löschen? Alle zugehörigen Daten werden gelöscht!`)) return
    try {
      await departmentsApi.delete(id)
      setDepartments((prev) => prev.filter((d) => d.id !== id))
    } catch {
      setError('Fehler beim Löschen.')
    }
  }

  return (
    <Layout>
      <div className="space-y-6 max-w-2xl">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Fachbereiche</h1>
          <button
            onClick={() => setIsAdding(true)}
            className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
          >
            <Plus size={18} /> Neu
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        )}

        {/* Neues Fachbereich Formular */}
        {isAdding && (
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="bg-white rounded-xl border border-primary-200 p-5 space-y-3"
          >
            <h3 className="font-semibold text-gray-900">Neuer Fachbereich</h3>
            <div>
              <input
                type="text"
                placeholder="Name (z.B. Wirtschaftsinformatik)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                {...register('name', { required: true })}
              />
            </div>
            <div>
              <input
                type="text"
                placeholder="Slug (URL-freundlich)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono"
                {...register('slug', { required: true })}
              />
              <p className="text-xs text-gray-400 mt-1">Wird automatisch aus dem Namen generiert.</p>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="bg-primary-600 text-white px-4 py-1.5 rounded-lg text-sm">
                Erstellen
              </button>
              <button
                type="button"
                onClick={() => { setIsAdding(false); reset() }}
                className="px-4 py-1.5 border border-gray-300 rounded-lg text-sm"
              >
                Abbrechen
              </button>
            </div>
          </form>
        )}

        {/* Liste */}
        <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
          {departments.length === 0 && (
            <p className="p-6 text-gray-500 text-center">Noch keine Fachbereiche angelegt.</p>
          )}
          {departments.map((dept) => (
            <div key={dept.id} className="flex justify-between items-center px-5 py-3">
              <div>
                <p className="font-medium text-gray-900">{dept.name}</p>
                <p className="text-xs text-gray-400 font-mono">{dept.slug}</p>
              </div>
              <button
                onClick={() => handleDelete(dept.id, dept.name)}
                className="text-red-400 hover:text-red-600 transition-colors"
                title="Löschen"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  )
}
