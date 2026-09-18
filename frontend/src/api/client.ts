import type {
  ApplicationDetail,
  ApplicationStats,
  ApplicationStatus,
  ApplicationSummary,
  BaseProfile,
  PendingReviewPayload,
  ScanSummary,
  SearchSettings,
} from './types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = body.detail ?? detail
    } catch {
      // body wasn't JSON — fall back to statusText
    }
    throw new ApiError(response.status, detail)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function triggerScan(): Promise<ScanSummary> {
  return request<ScanSummary>('/scan', { method: 'POST' })
}

export function listApplications(status?: ApplicationStatus): Promise<ApplicationSummary[]> {
  const query = status ? `?status=${status}` : ''
  return request<ApplicationSummary[]>(`/applications${query}`)
}

export function getApplication(id: string): Promise<ApplicationDetail> {
  return request<ApplicationDetail>(`/applications/${id}`)
}

export function getApplicationStats(): Promise<ApplicationStats> {
  return request<ApplicationStats>('/applications/stats')
}

export function deleteApplication(id: string): Promise<void> {
  return request<void>(`/applications/${id}`, { method: 'DELETE' })
}

export function submitProjectSelection(
  id: string,
  action: 'approve' | 'decline',
  selectedRepoNames: string[],
): Promise<{ application_id: string; next_review: PendingReviewPayload | null }> {
  return request(`/applications/${id}/project-selection`, {
    method: 'POST',
    body: JSON.stringify({ action, selected_repo_names: selectedRepoNames }),
  })
}

export function submitFinalApproval(
  id: string,
  action: 'approve' | 'decline',
): Promise<{ application_id: string; next_review: PendingReviewPayload | null }> {
  return request(`/applications/${id}/final-approval`, {
    method: 'POST',
    body: JSON.stringify({ action }),
  })
}

export function updateStatus(id: string, status: ApplicationStatus): Promise<ApplicationSummary> {
  return request<ApplicationSummary>(`/applications/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}

export function resumePdfUrl(id: string): string {
  return `${BASE_URL}/applications/${id}/resume.pdf`
}

export async function getProfile(): Promise<BaseProfile | null> {
  try {
    return await request<BaseProfile>('/profile')
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null
    throw error
  }
}

export function saveProfile(profile: BaseProfile): Promise<BaseProfile> {
  return request<BaseProfile>('/profile', { method: 'PUT', body: JSON.stringify(profile) })
}

export function getSearchSettings(): Promise<SearchSettings> {
  return request<SearchSettings>('/search-settings')
}

export function saveSearchSettings(settings: SearchSettings): Promise<SearchSettings> {
  return request<SearchSettings>('/search-settings', { method: 'PUT', body: JSON.stringify(settings) })
}
