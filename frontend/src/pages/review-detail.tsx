import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  FileSearch, 
  CheckCircle, 
  XCircle, 
  Clock,
  AlertTriangle,
  AlertCircle,
  Info
} from 'lucide-react'
import { apiClient } from '@/api/client'
import type { Review, Issue } from '@/types'

function ReviewDetail() {
  const { id } = useParams<{ id: string }>()

  const { data: review, isLoading: reviewLoading } = useQuery<Review>({
    queryKey: ['review', id],
    queryFn: async () => {
      const res = await apiClient.get(`/reviews/${id}`)
      return res.data
    },
    refetchInterval: (query) => {
      const d = query.state.data
      return d?.status === 'running' || d?.status === 'pending' ? 2000 : false
    }
  })

  const { data: issues } = useQuery<Issue[]>({
    queryKey: ['review-issues', id],
    queryFn: async () => {
      const res = await apiClient.get(`/reviews/${id}/issues`)
      return res.data.issues
    },
    enabled: !!review && review.status === 'completed'
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />
      case 'failed':
        return <XCircle className="w-6 h-6 text-red-500" />
      case 'running':
        return <Clock className="w-6 h-6 text-blue-500 animate-spin" />
      default:
        return <Clock className="w-6 h-6 text-yellow-500" />
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="w-5 h-5 text-red-500" />
      case 'warning':
        return <AlertCircle className="w-5 h-5 text-orange-500" />
      default:
        return <Info className="w-5 h-5 text-blue-500" />
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'border-l-red-500 bg-red-50'
      case 'warning':
        return 'border-l-orange-500 bg-orange-50'
      default:
        return 'border-l-blue-500 bg-blue-50'
    }
  }

  if (reviewLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!review) {
    return (
      <div className="text-center py-12">
        <XCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
        <h2 className="text-xl font-semibold">Review not found</h2>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            {getStatusIcon(review.status)}
            <h1 className="text-3xl font-bold">Review #{review.id.slice(0, 8)}</h1>
          </div>
          <p className="text-muted-foreground">
            {review.source_branch} → {review.target_branch}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-muted-foreground">
            {new Date(review.created_at).toLocaleString()}
          </p>
          {review.use_rag && (
            <span className="inline-block mt-2 px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
              RAG Enhanced
            </span>
          )}
        </div>
      </div>

      {/* Progress */}
      {review.status === 'running' && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-3">
            <Clock className="w-5 h-5 text-blue-500 animate-spin" />
            <span className="font-medium text-blue-700">Review in progress...</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all"
              style={{ 
                width: `${review.total_files > 0 
                  ? (review.processed_files / review.total_files) * 100 
                  : 0}%` 
              }}
            ></div>
          </div>
          <p className="text-sm text-blue-600 mt-2">
            Analyzing {review.processed_files} of {review.total_files} files
          </p>
        </div>
      )}

      {/* Summary Stats */}
      {review.status === 'completed' && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-sm text-muted-foreground">Total Issues</p>
            <p className="text-2xl font-bold">{review.total_issues}</p>
          </div>
          <div className="bg-red-50 border border-red-100 rounded-lg p-4">
            <p className="text-sm text-red-600">Critical</p>
            <p className="text-2xl font-bold text-red-700">{review.critical_issues}</p>
          </div>
          <div className="bg-orange-50 border border-orange-100 rounded-lg p-4">
            <p className="text-sm text-orange-600">Warnings</p>
            <p className="text-2xl font-bold text-orange-700">{review.warning_issues}</p>
          </div>
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
            <p className="text-sm text-blue-600">Info</p>
            <p className="text-2xl font-bold text-blue-700">{review.info_issues}</p>
          </div>
        </div>
      )}

      {/* Issues List */}
      {review.status === 'completed' && (
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="p-6 border-b border-border">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <FileSearch className="w-5 h-5" />
              Issues Found
            </h2>
          </div>

          {!issues || issues.length === 0 ? (
            <div className="p-8 text-center">
              <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
              <p className="text-lg font-medium">No issues found!</p>
              <p className="text-muted-foreground">Your code looks great</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {issues.map((issue) => (
                <div 
                  key={issue.id} 
                  className={`p-6 border-l-4 ${getSeverityColor(issue.severity)}`}
                >
                  <div className="flex items-start gap-3">
                    {getSeverityIcon(issue.severity)}
                    <div className="flex-1">
                      <h3 className="font-semibold">{issue.title}</h3>
                      <p className="text-sm text-muted-foreground mt-1">
                        {issue.file_path}
                        {issue.line_start && `:${issue.line_start}`}
                        {issue.line_end && issue.line_end !== issue.line_start && `-${issue.line_end}`}
                      </p>
                      {issue.details && (
                        <p className="text-sm mt-2">{issue.details}</p>
                      )}
                      {issue.affected_code && (
                        <pre className="mt-3 p-3 bg-black text-white rounded text-sm overflow-x-auto">
                          <code>{issue.affected_code}</code>
                        </pre>
                      )}
                      {issue.proposal && (
                        <div className="mt-3">
                          <p className="text-sm font-medium text-green-600">Suggested fix:</p>
                          <pre className="mt-1 p-3 bg-green-900 text-white rounded text-sm overflow-x-auto">
                            <code>{issue.proposal}</code>
                          </pre>
                        </div>
                      )}
                      {issue.tags.length > 0 && (
                        <div className="flex gap-2 mt-3">
                          {issue.tags.map((tag) => (
                            <span 
                              key={tag}
                              className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {review.status === 'failed' && review.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="font-semibold text-red-700 mb-2">Review Failed</h3>
          <p className="text-red-600">{review.error_message}</p>
        </div>
      )}
    </div>
  )
}

export default ReviewDetail
