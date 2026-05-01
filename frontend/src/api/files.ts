import axios from 'axios'
import apiClient from './client'
import type { UploadedFile } from '@/types'

export const filesApi = {
  /**
   * Pre-signed Upload-URL anfordern.
   * Gibt { upload_url, s3_key } zurück.
   */
  getUploadUrl: (data: {
    assignment_id: number
    filename: string
    content_type: string
    size_bytes: number
  }) =>
    apiClient
      .post<{ upload_url: string; s3_key: string }>('/v1/files/upload-url', data)
      .then((r) => r.data),

  /**
   * Datei direkt zu S3 hochladen (ohne API Gateway / Lambda).
   * Nutzt axios ohne den apiClient (kein Auth-Header → S3 will nur die URL).
   */
  uploadToS3: (uploadUrl: string, file: File, onProgress?: (percent: number) => void) =>
    axios.put(uploadUrl, file, {
      headers: { 'Content-Type': file.type },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total))
        }
      },
    }),

  /**
   * Upload-Abschluss bestätigen. Backend speichert Datei-Metadaten in DB.
   */
  confirmUpload: (data: {
    assignment_id: number
    s3_key: string
    filename: string
    content_type: string
    size_bytes: number
  }) =>
    apiClient.post<UploadedFile>('/v1/files/confirm', data).then((r) => r.data),

  /**
   * Download-URL für eine Datei anfordern.
   */
  getDownloadUrl: (fileId: number) =>
    apiClient.get<UploadedFile>(`/v1/files/${fileId}/download`).then((r) => r.data),
}
