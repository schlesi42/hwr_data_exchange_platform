/**
 * Nutzerverwaltung (Admin).
 * Nutzer anlegen, deaktivieren, Fachbereich zuweisen.
 */
import { useEffect, useState } from 'react'
import { Plus, UserX, UserCheck } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { usersApi } from '@/api/users'
import { departmentsApi } from '@/api/departments'
import { Layout } from '@/components/Layout'
import type { User, Department, UserRole } from '@/types'

interface UserForm {
  email: string
  name: string
  role: UserRole
  department_id: string
}

const ROLE_LABELS: Record<UserRole, string> = {
  admin: 'Administrator',
  buero: 'Fachbereichsbüro',
  dozent: 'Dozent/in',
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [isAdding, setIsAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { register, handleSubmit, reset } = useForm<UserForm>()

  useEffect(() => {
    Promise.all([usersApi.list(), departmentsApi.list()]).then(([u, d]) => {
      setUsers(u)
      setDepartments(d)
    })
  }, [])

  async function onSubmit(data: UserForm) {
    try {
      const user = await usersApi.create({
        email: data.email,
        name: data.name || undefined,
        role: data.role,
        department_id: data.department_id ? parseInt(data.department_id) : undefined,
      })
      setUsers((prev) => [...prev, user])
      reset()
      setIsAdding(false)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Fehler.'
      setError(msg)
    }
  }

  async function toggleActive(user: User) {
    const updated = await usersApi.update(user.id, { is_active: !user.is_active })
    setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)))
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Nutzerverwaltung</h1>
          <button
            onClick={() => setIsAdding(true)}
            className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
          >
            <Plus size={18} /> Nutzer anlegen
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        )}

        {/* Formular */}
        {isAdding && (
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="bg-white rounded-xl border border-primary-200 p-5 space-y-3"
          >
            <h3 className="font-semibold">Neuen Nutzer anlegen</h3>
            <p className="text-sm text-gray-500">
              Eine Einladungs-E-Mail mit temporärem Passwort wird automatisch versandt.
            </p>
            <div className="grid grid-cols-2 gap-3">
              <input
                type="email"
                placeholder="E-Mail *"
                className="col-span-2 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                {...register('email', { required: true })}
              />
              <input
                type="text"
                placeholder="Name (optional)"
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                {...register('name')}
              />
              <select
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                {...register('role', { required: true })}
              >
                <option value="">Rolle wählen *</option>
                <option value="admin">Administrator</option>
                <option value="buero">Fachbereichsbüro</option>
                <option value="dozent">Dozent/in</option>
              </select>
              <select
                className="col-span-2 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                {...register('department_id')}
              >
                <option value="">Kein Fachbereich (Admin)</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="bg-primary-600 text-white px-4 py-1.5 rounded-lg text-sm">
                Anlegen & einladen
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

        {/* Tabelle */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left py-3 px-4 font-medium text-gray-600">E-Mail</th>
                <th className="text-left py-3 px-4 font-medium text-gray-600">Name</th>
                <th className="text-left py-3 px-4 font-medium text-gray-600">Rolle</th>
                <th className="text-left py-3 px-4 font-medium text-gray-600">Fachbereich</th>
                <th className="text-left py-3 px-4 font-medium text-gray-600">Status</th>
                <th className="py-3 px-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map((u) => (
                <tr key={u.id} className={`hover:bg-gray-50 ${!u.is_active ? 'opacity-50' : ''}`}>
                  <td className="py-3 px-4 font-medium">{u.email}</td>
                  <td className="py-3 px-4 text-gray-600">{u.name || '–'}</td>
                  <td className="py-3 px-4 text-gray-600">{ROLE_LABELS[u.role]}</td>
                  <td className="py-3 px-4 text-gray-600">{u.department_name || '–'}</td>
                  <td className="py-3 px-4">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${u.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {u.is_active ? 'Aktiv' : 'Deaktiviert'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => toggleActive(u)}
                      className="text-gray-400 hover:text-gray-600"
                      title={u.is_active ? 'Deaktivieren' : 'Aktivieren'}
                    >
                      {u.is_active ? <UserX size={16} /> : <UserCheck size={16} />}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  )
}
