import { useQuery } from '@tanstack/react-query'
import { FileSearch, ArrowRight, Clock, CheckCircle, XCircle } from 'lucide-react'
import { apiClient } from '@/api/client'
import type { Review } from '@/types'

function Reviews() {
  const { data: reviews, isLoading } = useQuery<Review[]>({
    queryKey: ['reviews'],
    queryFn: async () => {
      const res = await apiClient.get('/reviews/')
      return res.data.reviews
    }
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'running':
        return <Clock className="w-5 h-5 text-blue-500 animate-spin" />
      default:
        return <Clock className="w-5 h-5 text-yellow-500" />
    }
  }

  const getSeverityBadge = (review: Review) => {
    if (review.critical_issues > 0) {
      return (
        <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">
          {review.critical_issues} Critical
        </span>
      )
    } else if (review.warning_issues > 0) {
      return (
        <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs font-medium">
          {review.warning_issues} Warnings
        </span>
      )
    } else if (review.total_issues > 0) {
      return (
        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
          {review.total_issues} Info
        </span>
      )
    }
    return (
      <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
        No Issues
      </span>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Reviews</h1>
          <p className="text-muted-foreground mt-1">
            View all code review reports
          </p>
        </div>
        <a
          href="/new-review"
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors flex items-center gap-2"
        >
          <FileSearch className="w-4 h-4" />
          New Review
        </a>
      </div>

      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-6 border-b border-border">
          <h2 className="text-lg font-semibold">All Reviews</h2>
        </div>

        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          </div>
        ) : reviews?.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            <FileSearch className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No reviews yet</p>
            <p className="text-sm">Start a new review to analyze your code</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {reviews?.map((review) => (
              <a
                key={review.id}
                href={`/reviews/${review.id}`}
                className="p-6 flex items-center justify-between hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  {getStatusIcon(review.status)}
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">Review #{review.id.slice(0, 8)}</h3>
                      {getSeverityBadge(review)}
                      {review.use_rag && (
                        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">
                          RAG
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {review.source_branch} → {review.target_branch} • {review.processed_files} files
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(review.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <ArrowRight className="w-5 h-5 text-muted-foreground" />
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Reviews
