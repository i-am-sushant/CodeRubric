import { useQuery } from '@tanstack/react-query'
import { 
  GitBranch, 
  FileSearch, 
  AlertTriangle, 
  TrendingUp,
  Activity
} from 'lucide-react'
import { apiClient } from '@/api/client'
import type { Stats } from '@/types'

function Dashboard() {
  const { data: stats, isLoading } = useQuery<Stats>({
    queryKey: ['stats'],
    queryFn: async () => {
      const res = await apiClient.get('/stats/')
      return res.data
    }
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  const statCards = [
    { 
      label: 'Repositories', 
      value: stats?.total_repositories || 0, 
      icon: GitBranch,
      color: 'bg-blue-500'
    },
    { 
      label: 'Total Reviews', 
      value: stats?.total_reviews || 0, 
      icon: FileSearch,
      color: 'bg-green-500'
    },
    { 
      label: 'Issues Found', 
      value: stats?.total_issues_found || 0, 
      icon: AlertTriangle,
      color: 'bg-orange-500'
    },
    { 
      label: 'Avg Issues/Review', 
      value: stats?.average_issues_per_review?.toFixed(1) || '0', 
      icon: TrendingUp,
      color: 'bg-purple-500'
    },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Overview of your code review activity
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.label} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  <p className="text-2xl font-bold mt-1">{stat.value}</p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Review Activity</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Activity className="w-5 h-5 text-muted-foreground" />
                <span>Last 7 days</span>
              </div>
              <span className="font-semibold">{stats?.reviews_last_7_days || 0} reviews</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Activity className="w-5 h-5 text-muted-foreground" />
                <span>Last 30 days</span>
              </div>
              <span className="font-semibold">{stats?.reviews_last_30_days || 0} reviews</span>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <a 
              href="/new-review" 
              className="flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-accent transition-colors"
            >
              <div className="bg-primary p-2 rounded">
                <FileSearch className="w-4 h-4 text-primary-foreground" />
              </div>
              <div>
                <p className="font-medium">Start New Review</p>
                <p className="text-sm text-muted-foreground">Analyze code with RAG context</p>
              </div>
            </a>
            <a 
              href="/repos" 
              className="flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-accent transition-colors"
            >
              <div className="bg-secondary p-2 rounded">
                <GitBranch className="w-4 h-4 text-secondary-foreground" />
              </div>
              <div>
                <p className="font-medium">Add Repository</p>
                <p className="text-sm text-muted-foreground">Index a new codebase for review</p>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
