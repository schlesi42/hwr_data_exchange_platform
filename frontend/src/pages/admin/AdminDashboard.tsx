/**
 * Admin-Dashboard – Überblick über die gesamte Plattform.
 */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Building2, Users, FileText, Settings } from 'lucide-react'
import { departmentsApi } from '@/api/departments'
import { usersApi } from '@/api/users'
import { requestsApi } from '@/api/requests'
import { Layout } from '@/components/Layout'

export default function AdminDashboard() {
  const [stats, setStats] = useState({ departments: 0, users: 0, requests: 0 })

  useEffect(() => {
    Promise.all([
      departmentsApi.list(),
      usersApi.list(),
      requestsApi.list(),
    ]).then(([depts, users, requests]) => {
      setStats({
        departments: depts.length,
        users: users.length,
        requests: requests.length,
      })
    })
  }, [])

  const tiles = [
    {
      icon: <Building2 size={28} className="text-blue-500" />,
      title: 'Fachbereiche',
      count: stats.departments,
      link: '/admin/departments',
      description: 'Fachbereiche verwalten',
    },
    {
      icon: <Users size={28} className="text-green-500" />,
      title: 'Nutzer',
      count: stats.users,
      link: '/admin/users',
      description: 'Nutzer verwalten',
    },
    {
      icon: <FileText size={28} className="text-purple-500" />,
      title: 'Anforderungen',
      count: stats.requests,
      link: '/admin/requests',
      description: 'Alle Anforderungen',
    },
    {
      icon: <Settings size={28} className="text-gray-500" />,
      title: 'Templates',
      count: null,
      link: '/admin/templates',
      description: 'E-Mail-Templates verwalten',
    },
  ]

  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Admin-Dashboard</h1>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {tiles.map((tile) => (
            <Link
              key={tile.link}
              to={tile.link}
              className="bg-white rounded-xl border border-gray-200 p-6 hover:border-primary-300 hover:shadow-md transition-all"
            >
              <div className="flex items-center gap-3 mb-3">
                {tile.icon}
                <span className="font-semibold text-gray-900">{tile.title}</span>
              </div>
              {tile.count !== null && (
                <div className="text-3xl font-bold text-gray-900 mb-1">{tile.count}</div>
              )}
              <div className="text-sm text-gray-500">{tile.description}</div>
            </Link>
          ))}
        </div>
      </div>
    </Layout>
  )
}
