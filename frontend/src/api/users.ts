import apiClient from './client'
import type { User, UserRole } from '@/types'

export const usersApi = {
  me: () =>
    apiClient.get<User>('/v1/users/me').then((r) => r.data),

  list: (params?: { department_id?: number; role?: UserRole }) =>
    apiClient.get<User[]>('/v1/users', { params }).then((r) => r.data),

  create: (data: { email: string; name?: string; role: UserRole; department_id?: number }) =>
    apiClient.post<User>('/v1/users', data).then((r) => r.data),

  update: (id: number, data: Partial<{ name: string; is_active: boolean; department_id: number }>) =>
    apiClient.put<User>(`/v1/users/${id}`, data).then((r) => r.data),
}
