import apiClient from './client'
import type { DocumentRequest, DocumentRequestSummary } from '@/types'

export const requestsApi = {
  list: () =>
    apiClient.get<DocumentRequestSummary[]>('/v1/requests').then((r) => r.data),

  get: (id: number) =>
    apiClient.get<DocumentRequest>(`/v1/requests/${id}`).then((r) => r.data),

  create: (data: {
    title: string
    description?: string
    deadline: string
    dozent_ids: number[]
  }) =>
    apiClient.post<DocumentRequest>('/v1/requests', data).then((r) => r.data),

  update: (id: number, data: Partial<{ title: string; description: string; deadline: string }>) =>
    apiClient.put<DocumentRequest>(`/v1/requests/${id}`, data).then((r) => r.data),

  delete: (id: number) =>
    apiClient.delete(`/v1/requests/${id}`),
}
