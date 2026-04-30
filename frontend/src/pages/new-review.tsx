import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { FileSearch, GitBranch, Loader2 } from 'lucide-react'
import { apiClient } from '@/api/client'
import type { Repository } from '@/types'

function NewReview() {
  const [searchParams] = useSearchParams()
  const preselectedRepo = searchParams.get('repo')
  
  const [selectedRepo, setSelectedRepo] = useState(preselectedRepo || '')
  const [sourceBranch, setSourceBranch] = useState('HEAD')
  const [targetBranch, setTargetBranch] = useState('main')
  const [useRag, setUseRag] = useState(true)
  const queryClient = useQueryClient()

  const { data: repos } = useQuery<Repository[]>({
    queryKey: ['repositories'],
    queryFn: async () => {
      const res = await apiClient.get('/repos/')
      return res.data.repositories
    }
  })

  const createReviewMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post('/reviews/', {
        repo_id: selectedRepo,
        source_branch: sourceBranch,
        target_branch: targetBranch,
        use_rag: useRag
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
    createReviewMutation.mutate()
  }

  const indexedRepos = repos?.filter(r => r.index_status === 'completed') || []

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">New Code Review</h1>
        <p className="text-muted-foreground mt-1">
          Analyze code changes with AI-powered review and RAG context
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Repository Selection */}
        <div className="bg-card border border-border rounded-lg p-6">
          <label className="block text-sm font-medium mb-2">
            Select Repository
          </label>
          <select
            value={selectedRepo}
            onChange={(e) => setSelectedRepo(e.target.value)}
            required
            className="w-full px-4 py-2 border border-border rounded-lg bg-background"
          >
            <option value="">Choose a repository...</option>
            {indexedRepos.map((repo) => (
              <option key={repo.id} value={repo.id}>
                {repo.name} ({repo.chunks_count} chunks indexed)
              </option>
            ))}
          </select>
          {indexedRepos.length === 0 && (
            <p className="text-sm text-muted-foreground mt-2">
              No indexed repositories found.{' '}
              <a href="/repos" className="text-primary hover:underline">
                Add a repository first
              </a>
            </p>
          )}
        </div>

        {/* Branch Configuration */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="font-medium mb-4 flex items-center gap-2">
            <GitBranch className="w-4 h-4" />
            Branch Configuration
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Source Branch</label>
              <input
                type="text"
                value={sourceBranch}
                onChange={(e) => setSourceBranch(e.target.value)}
                placeholder="HEAD or feature-branch"
                className="w-full px-4 py-2 border border-border rounded-lg bg-background"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Branch to review (or HEAD for current)
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Target Branch</label>
              <input
                type="text"
                value={targetBranch}
                onChange={(e) => setTargetBranch(e.target.value)}
                placeholder="main or master"
                className="w-full px-4 py-2 border border-border rounded-lg bg-background"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Base branch for comparison
              </p>
            </div>
          </div>
        </div>

        {/* RAG Toggle */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">Enable RAG Context</h3>
              <p className="text-sm text-muted-foreground">
                Use Retrieval-Augmented Generation for context-aware review
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
          disabled={!selectedRepo || createReviewMutation.isPending}
          className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {createReviewMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Starting Review...
            </>
          ) : (
            <>
              <FileSearch className="w-4 h-4" />
              Start Code Review
            </>
          )}
        </button>
      </form>
    </div>
  )
}

export default NewReview
