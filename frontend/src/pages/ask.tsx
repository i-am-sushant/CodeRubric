import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { MessageCircleQuestion, Send, Loader2, GitBranch } from 'lucide-react'
import { apiClient } from '@/api/client'
import type { Repository } from '@/types'

function Ask() {
  const [selectedRepo, setSelectedRepo] = useState('')
  const [question, setQuestion] = useState('')
  const [sourceBranch, setSourceBranch] = useState('HEAD')
  const [targetBranch, setTargetBranch] = useState('main')
  const [filters, setFilters] = useState('')
  const [answer, setAnswer] = useState<string | null>(null)

  const { data: repos } = useQuery<Repository[]>({
    queryKey: ['repositories'],
    queryFn: async () => {
      const res = await apiClient.get('/repos/')
      return res.data.repositories
    }
  })

  const clonedRepos = repos?.filter(r => r.local_path) || []

  const askMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post('/ask/', {
        repo_id: selectedRepo,
        question,
        source_branch: sourceBranch,
        target_branch: targetBranch,
        filters: filters || ''
      })
      return res.data
    },
    onSuccess: (data) => {
      setAnswer(data.answer)
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setAnswer(null)
    askMutation.mutate()
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <MessageCircleQuestion className="w-8 h-8 text-blue-500" />
          <h1 className="text-3xl font-bold">Ask About Code</h1>
        </div>
        <p className="text-muted-foreground mt-1">
          Ask any question about code changes in a repository — powered by gito
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Repository Selection */}
        <div className="bg-card border border-border rounded-lg p-6">
          <label className="block text-sm font-medium mb-2">Repository</label>
          <select
            value={selectedRepo}
            onChange={(e) => setSelectedRepo(e.target.value)}
            required
            className="w-full px-4 py-2 border border-border rounded-lg bg-background"
          >
            <option value="">Choose a repository...</option>
            {clonedRepos.map((repo) => (
              <option key={repo.id} value={repo.id}>
                {repo.name}
              </option>
            ))}
          </select>
          {clonedRepos.length === 0 && (
            <p className="text-sm text-muted-foreground mt-2">
              No cloned repositories found.{' '}
              <a href="/repos" className="text-primary hover:underline">
                Add a repository first
              </a>
            </p>
          )}
        </div>

        {/* Branch Config */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="font-medium mb-4 flex items-center gap-2">
            <GitBranch className="w-4 h-4" />
            Diff Context
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
            </div>
          </div>
          <div className="mt-3">
            <label className="block text-sm font-medium mb-1">File Filters</label>
            <input
              type="text"
              value={filters}
              onChange={(e) => setFilters(e.target.value)}
              placeholder="e.g. *.py, src/**/*.ts (optional)"
              className="w-full px-4 py-2 border border-border rounded-lg bg-background"
            />
          </div>
        </div>

        {/* Question */}
        <div className="bg-card border border-border rounded-lg p-6">
          <label className="block text-sm font-medium mb-2">Your Question</label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. What does this change do? Are there any security concerns? Summarize the changes..."
            required
            rows={4}
            className="w-full px-4 py-2 border border-border rounded-lg bg-background resize-none"
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={askMutation.isPending || !selectedRepo || !question.trim()}
          className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {askMutation.isPending ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Thinking...
            </>
          ) : (
            <>
              <Send className="w-5 h-5" />
              Ask
            </>
          )}
        </button>

        {askMutation.isError && (
          <p className="text-sm text-red-500 text-center">
            {(askMutation.error as Error).message || 'Failed to get answer'}
          </p>
        )}
      </form>

      {/* Answer */}
      {answer && (
        <div className="mt-8 bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <MessageCircleQuestion className="w-5 h-5 text-blue-500" />
            Answer
          </h2>
          <div className="prose prose-sm max-w-none dark:prose-invert whitespace-pre-wrap">
            {answer}
          </div>
        </div>
      )}
    </div>
  )
}

export default Ask
