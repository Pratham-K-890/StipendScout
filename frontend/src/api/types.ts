export type ApplicationStatus = 'pending' | 'applied' | 'rejected' | 'interview' | 'stale'

export interface ApplicationSummary {
  id: string
  status: ApplicationStatus
  listing_title: string
  listing_company: string
  listing_url: string
  created_at: string
  status_changed_at: string
  applied_at: string | null
  stipend_amount: number | null
  role_tier: 'backend' | 'ml_data_science' | 'ai_agent_llm' | null
}

export interface ProjectCandidate {
  repo_name: string
  description: string | null
  readme_excerpt: string
  topics: string[]
  language: string | null
  url: string | null
  deployed_url: string | null
  is_private: boolean
  is_fork: boolean
  stars: number
  updated_at: string
}

export interface RankedProject {
  project: ProjectCandidate
  similarity: number
}

export interface TailoredBullet {
  text: string
  source_type: 'experience' | 'project' | 'hackathon' | 'responsibility'
  source_ref: string
  source_excerpt: string
  flagged_terms: string[]
}

export interface TailoredResumeLinks {
  linkedin: string | null
  github: string | null
  leetcode: string | null
  portfolio: string | null
}

export interface TailoredResume {
  name: string
  email: string
  phone: string | null
  location: string | null
  links: TailoredResumeLinks
  education_summary: string[]
  // category name -> skills in that category, in render order
  highlighted_skills: Record<string, string[]>
  bullets: TailoredBullet[]
}

export interface CoverLetter {
  body: string
  flagged_terms: string[]
}

export interface ProjectSelectionReviewPayload {
  type: 'project_selection'
  application_id: string
  ranked_projects: RankedProject[]
}

export interface FinalApprovalReviewPayload {
  type: 'final_approval'
  application_id: string
  tailored_resume: TailoredResume
  cover_letter: CoverLetter
}

export type PendingReviewPayload = ProjectSelectionReviewPayload | FinalApprovalReviewPayload

export interface PendingReview {
  application_id: string
  review_type: 'project_selection' | 'final_approval'
  payload: PendingReviewPayload
}

export interface ApplicationDetail extends ApplicationSummary {
  jd_snapshot: Record<string, unknown>
  listing_summary: JDSummary | null
  tailored_resume: TailoredResume | null
  tailored_cover_letter: string | null
  pending_review: PendingReviewPayload | null
}

export interface ScanSummary {
  sources_scraped: string[]
  new_applications_started: number
  pending_reviews: PendingReview[]
}

export interface ProfileLinks {
  linkedin: string | null
  github: string | null
  leetcode: string | null
  portfolio: string | null
}

export interface EducationEntry {
  institution: string
  degree: string
  branch: string | null
  start_year: number | null
  end_year: number | null
  cgpa: string | null
}

export interface ExperienceEntry {
  title: string
  company: string
  start_date: string
  end_date: string | null
  bullets: string[]
}

export interface HackathonEntry {
  title: string
  event: string
  team_project: boolean
  bullets: string[]
}

export interface ResponsibilityEntry {
  title: string
  organization: string
  bullets: string[]
}

export interface BaseProfile {
  name: string
  email: string
  phone: string | null
  location: string | null
  links: ProfileLinks
  education: EducationEntry[]
  experience: ExperienceEntry[]
  hackathons: HackathonEntry[]
  responsibilities: ResponsibilityEntry[]
  // category name -> skills in that category, in render order
  skills: Record<string, string[]>
}

export interface SearchSettings {
  search_queries: string[]
  exclude_keywords: string[]
}

export interface JDSummary {
  stipend_amount: number | null
  stipend_status: 'confirmed_ok' | 'confirmed_below_minimum' | 'unknown'
  location: string | null
  is_remote: boolean
  ppo_detected: boolean
  role_tier: 'backend' | 'ml_data_science' | 'ai_agent_llm' | null
  role_similarity: number | null
  responsibilities: string[]
  requirements: string[]
  duration: string | null
  benefits: string[]
}

export interface ApplicationStats {
  total: number
  by_status: Record<ApplicationStatus, number>
  response_rate: number | null
  avg_stipend: number | null
  role_tier_breakdown: Record<string, number>
}
