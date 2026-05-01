import apiClient from './client'
import type { Department, ReminderConfig } from '@/types'

export const departmentsApi = {
  list: () =>
    apiClient.get<Department[]>('/v1/departments').then((r) => r.data),

  create: (data: { name: string; slug: string }) =>
    apiClient.post<Department>('/v1/departments', data).then((r) => r.data),

  update: (id: number, data: Partial<{ name: string; slug: string }>) =>
    apiClient.put<Department>(`/v1/departments/${id}`, data).then((r) => r.data),

  delete: (id: number) =>
    apiClient.delete(`/v1/departments/${id}`),

  getReminderConfig: (id: number) =>
    apiClient.get<ReminderConfig>(`/v1/departments/${id}/reminder-config`).then((r) => r.data),

  updateReminderConfig: (id: number, data: Partial<ReminderConfig>) =>
    apiClient.put<ReminderConfig>(`/v1/departments/${id}/reminder-config`, data).then((r) => r.data),
}
