import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Zap, GitBranch, Loader2, Filter, Layers } from 'lucide-react'
import { apiClient } from '@/api/client'

function QuickReview() {
  const [repoUrl, setRepoUrl] = useState('')
  const [branch, setBranch] = useState('main')
  const [sourceBranch, setSourceBranch] = useState('HEAD')
  const [targetBranch, setTargetBranch] = useState('main')
  const [useRag, setUseRag] = useState(false)
  const [filters, setFilters] = useState('')
  const [reviewAll, setReviewAll] = useState(false)
  const queryClient = useQueryClient()

  const quickReviewMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post('/reviews/quick-review', {
        repo_url: repoUrl,
        branch,
        source_branch: sourceBranch,
        target_branch: targetBranch,
        use_rag: useRag,
        filters: filters || '',
        review_all: reviewAll
      })
      return res.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['reviews'] })
      window.location.href = `/reviews/${data.id}`
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    quickReviewMutation.mutate()
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Zap className="w-8 h-8 text-yellow-500" />
          <h1 className="text-3xl font-bold">Quick Review</h1>
        </div>
        <p className="text-muted-foreground mt-1">
          Paste a GitHub URL and get a code review instantly — no pre-indexing needed
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Repository URL */}
        <div className="bg-card border border-border rounded-lg p-6">
          <label className="block text-sm font-medium mb-2">
            Repository URL
          </label>
          <input
            type="text"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/owner/repo.git"
            required
            className="w-full px-4 py-2 border border-border rounded-lg bg-background"
          />
          <div className="mt-3">
            <label className="block text-sm font-medium mb-1">Clone Branch</label>
            <input
              type="text"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder="main"
              className="w-full px-4 py-2 border border-border rounded-lg bg-background"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Default branch to clone (e.g. main, master, develop)
            </p>
          </div>
        </div>

        {/* Branch Configuration */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="font-medium mb-4 flex items-center gap-2">
            <GitBranch className="w-4 h-4" />
            Diff Configuration
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Source</label>
              <input
                type="text"
                value={sourceBranch}
                onChange={(e) => setSourceBranch(e.target.value)}
                placeholder="HEAD"
                className="w-full px-4 py-2 border border-border rounded-lg bg-background"
              />
              <p className="text-xs text-muted-foreground mt-1">Branch to review</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Target</label>
              <input
                type="text"
                value={targetBranch}
                onChange={(e) => setTargetBranch(e.target.value)}
                placeholder="main"
                className="w-full px-4 py-2 border border-border rounded-lg bg-background"
              />
              <p className="text-xs text-muted-foreground mt-1">Base branch for comparison</p>
            </div>
          </div>
        </div>

        {/* File Filters */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="font-medium mb-4 flex items-center gap-2">
            <Filter className="w-4 h-4" />
            File Filters
          </h3>
          <input
            type="text"
            value={filters}
            onChange={(e) => setFilters(e.target.value)}
            placeholder="e.g. *.py, src/**/*.ts (comma-separated glob patterns)"
            className="w-full px-4 py-2 border border-border rounded-lg bg-background"
          />
          <p className="text-xs text-muted-foreground mt-1">
            Only review files matching these patterns. Leave empty for all files.
          </p>
        </div>

        {/* Review Options */}
        <div className="bg-card border border-border rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium flex items-center gap-2">
                <Layers className="w-4 h-4" />
                Review Entire Codebase
              </h3>
              <p className="text-sm text-muted-foreground">
                {reviewAll
                  ? 'Reviewing ALL files, not just changes'
                  : 'Only reviewing changes between branches'}
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={reviewAll}
                onChange={(e) => setReviewAll(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>

          <div className="border-t border-border" />

          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">Enable RAG Context</h3>
              <p className="text-sm text-muted-foreground">
                {useRag
                  ? 'Context-aware review (will index the repo first)'
                  : 'Standard review using only code diffs'}
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={useRag}
                onChange={(e) => setUseRag(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={quickReviewMutation.isPending || !repoUrl.trim()}
          className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {quickReviewMutation.isPending ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Cloning & Reviewing...
            </>
          ) : (
            <>
              <Zap className="w-5 h-5" />
              Start Quick Review
            </>
          )}
        </button>

        {quickReviewMutation.isError && (
          <p className="text-sm text-red-500 text-center">
            {(quickReviewMutation.error as Error).message || 'Failed to start review'}
          </p>
        )}
      </form>
    </div>
  )
}

export default QuickReview
