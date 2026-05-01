/**
 * StatusBadge – farbige Kennzeichnung des Status.
 */
import type { RequestStatus, AssignmentStatus } from '@/types'

const REQUEST_STATUS_CONFIG: Record<RequestStatus, { label: string; className: string }> = {
  open:      { label: 'Offen',         className: 'bg-blue-100 text-blue-800' },
  partial:   { label: 'Teilweise',     className: 'bg-yellow-100 text-yellow-800' },
  completed: { label: 'Vollständig',   className: 'bg-green-100 text-green-800' },
  overdue:   { label: 'Überfällig',    className: 'bg-red-100 text-red-800' },
}

const ASSIGNMENT_STATUS_CONFIG: Record<AssignmentStatus, { label: string; className: string }> = {
  pending:  { label: 'Ausstehend',  className: 'bg-gray-100 text-gray-800' },
  uploaded: { label: 'Hochgeladen', className: 'bg-green-100 text-green-800' },
  overdue:  { label: 'Überfällig',  className: 'bg-red-100 text-red-800' },
}

export function RequestStatusBadge({ status }: { status: RequestStatus }) {
  const config = REQUEST_STATUS_CONFIG[status]
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
      {config.label}
    </span>
  )
}

export function AssignmentStatusBadge({ status }: { status: AssignmentStatus }) {
  const config = ASSIGNMENT_STATUS_CONFIG[status]
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
      {config.label}
    </span>
  )
}
