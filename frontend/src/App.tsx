import { Routes, Route } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import { Layout } from '@/components/layout'
import Dashboard from '@/pages/dashboard'
import Repositories from '@/pages/repositories'
import Reviews from '@/pages/reviews'
import ReviewDetail from '@/pages/review-detail'
import NewReview from '@/pages/new-review'
import Settings from '@/pages/settings'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/repos" element={<Repositories />} />
        <Route path="/reviews" element={<Reviews />} />
        <Route path="/reviews/:id" element={<ReviewDetail />} />
        <Route path="/new-review" element={<NewReview />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
      <Toaster />
    </Layout>
  )
}

export default App
