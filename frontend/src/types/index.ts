/**
 * Zentrale TypeScript-Typen für die gesamte Frontend-Anwendung.
 * Diese Typen spiegeln die Pydantic-Schemas des Backends wider.
 */

export type UserRole = 'admin' | 'buero' | 'dozent'

export interface User {
  id: number
  email: string
  name: string | null
  role: UserRole
  department_id: number | null
  department_name: string | null
  is_active: boolean
  created_at: string
}

export interface Department {
  id: number
  name: string
  slug: string
  created_at: string
}

export interface ReminderConfig {
  id: number
  department_id: number
  days_before: string       // z.B. "7,3,1"
  send_overdue: boolean
  overdue_interval_days: number
}

export type RequestStatus = 'open' | 'partial' | 'completed' | 'overdue'
export type AssignmentStatus = 'pending' | 'uploaded' | 'overdue'

export interface UploadedFile {
  id: number
  filename: string
  size_bytes: number
  content_type: string
  uploaded_at: string
  download_url?: string     // temporäre S3-URL (nur bei Bedarf befüllt)
}

export interface Assignment {
  id: number
  request_id: number
  dozent_id: number
  dozent_email: string
  dozent_name: string | null
  status: AssignmentStatus
  submitted_at: string | null
  files: UploadedFile[]
}

export interface DocumentRequest {
  id: number
  title: string
  description: string | null
  department_id: number
  department_name: string
  created_by: number
  deadline: string
  status: RequestStatus
  created_at: string
  updated_at: string
  assignments: Assignment[]
}

export interface DocumentRequestSummary {
  id: number
  title: string
  department_id: number
  department_name: string
  deadline: string
  status: RequestStatus
  created_at: string
  total_assignments: number
  uploaded_count: number
}

export type EmailTemplateType = 'invitation' | 'request' | 'reminder' | 'overdue'

export interface EmailTemplate {
  id: number
  department_id: number | null
  type: EmailTemplateType
  subject: string
  body_html: string
  created_at: string
  updated_at: string
}
