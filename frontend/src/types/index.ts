export interface Repository {
  id: string
  name: string
  url: string | null
  local_path: string | null
  indexed_at: string | null
  index_status: 'pending' | 'indexing' | 'completed' | 'failed'
  chunks_count: number
  created_at: string
  updated_at: string
}

export interface Review {
  id: string
  repo_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  target_branch: string
  source_branch: string
  use_rag: boolean
  total_files: number
  processed_files: number
  total_issues: number
  critical_issues: number
  warning_issues: number
  info_issues: number
  error_message: string | null
  started_at: string
  completed_at: string | null
  created_at: string
}

export interface Issue {
  id: string
  review_id: string
  file_path: string
  title: string
  details: string | null
  severity: 'critical' | 'warning' | 'info'
  line_start: number | null
  line_end: number | null
  tags: string[]
  affected_code: string | null
  proposal: string | null
  score: number | null
  created_at: string
}

export interface Stats {
  total_repositories: number
  total_reviews: number
  total_issues_found: number
  average_issues_per_review: number
  reviews_last_7_days: number
  reviews_last_30_days: number
}

export interface ReviewProgress {
  processed_files: number
  total_files: number
  percent_complete: number
  current_file: string | null
  status: string
}
