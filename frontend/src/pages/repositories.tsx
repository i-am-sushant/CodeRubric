import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  GitBranch, 
  Plus, 
  RefreshCw, 
  Trash2, 
  CheckCircle, 
  XCircle,
  Clock
} from 'lucide-react'
import { apiClient } from '@/api/client'
import type { Repository } from '@/types'

function Repositories() {
  const [newRepoUrl, setNewRepoUrl] = useState('')
  const queryClient = useQueryClient()

  const { data: repos, isLoading } = useQuery<Repository[]>({
    queryKey: ['repositories'],
    queryFn: async () => {
      const res = await apiClient.get('/repos/')
      return res.data.repositories
    }
  })

  const addRepoMutation = useMutation({
    mutationFn: async (url: string) => {
      const res = await apiClient.post('/repos/', {
        repo_url: url,
        branch: 'main'
      })
      return res.data
    },
    onSuccess: () => {
      setNewRepoUrl('')
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
    }
  })

  const deleteRepoMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/repos/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
    }
  })

  const handleAddRepo = (e: React.FormEvent) => {
    e.preventDefault()
    if (newRepoUrl.trim()) {
      addRepoMutation.mutate(newRepoUrl.trim())
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'indexing':
        return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />
      default:
        return <Clock className="w-5 h-5 text-yellow-500" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Repositories</h1>
          <p className="text-muted-foreground mt-1">
            Manage code repositories for RAG-based review
          </p>
        </div>
      </div>

      {/* Add Repository Form */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Add Repository</h2>
        <form onSubmit={handleAddRepo} className="flex gap-4">
          <input
            type="text"
            placeholder="https://github.com/owner/repo.git"
            value={newRepoUrl}
            onChange={(e) => setNewRepoUrl(e.target.value)}
            className="flex-1 px-4 py-2 border border-border rounded-lg bg-background"
          />
          <button
            type="submit"
            disabled={addRepoMutation.isPending || !newRepoUrl.trim()}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium disabled:opacity-50 flex items-center gap-2"
          >
            {addRepoMutation.isPending ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            Add
          </button>
        </form>
        <p className="text-sm text-muted-foreground mt-2">
          Repository will be cloned and indexed for RAG context retrieval
        </p>
      </div>

      {/* Repository List */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-6 border-b border-border">
          <h2 className="text-lg font-semibold">Your Repositories</h2>
        </div>
        
        {isLoading ? (
          <div className="p-8 text-center">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-muted-foreground" />
          </div>
        ) : repos?.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            <GitBranch className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No repositories added yet</p>
            <p className="text-sm">Add a repository to start analyzing code</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {repos?.map((repo) => (
              <div key={repo.id} className="p-6 flex items-center justify-between hover:bg-accent/50 transition-colors">
                <div className="flex items-center gap-4">
                  <GitBranch className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <h3 className="font-semibold">{repo.name}</h3>
                    <p className="text-sm text-muted-foreground">{repo.url}</p>
                    <div className="flex items-center gap-4 mt-1 text-sm">
                      <span className="flex items-center gap-1">
                        {getStatusIcon(repo.index_status)}
                        <span className="capitalize">{repo.index_status}</span>
                      </span>
                      {repo.chunks_count > 0 && (
                        <span className="text-muted-foreground">
                          {repo.chunks_count} chunks indexed
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {repo.index_status === 'completed' && (
                    <a
                      href={`/new-review?repo=${repo.id}`}
                      className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg text-sm font-medium hover:bg-secondary/80 transition-colors"
                    >
                      Review
                    </a>
                  )}
                  <button
                    onClick={() => deleteRepoMutation.mutate(repo.id)}
                    disabled={deleteRepoMutation.isPending}
                    className="p-2 text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Repositories
