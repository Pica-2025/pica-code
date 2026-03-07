import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import TesterSession from './pages/TesterSession'
import ResultsPage from './pages/ResultsPage'
import ImageDetail from './pages/ImageDetail'
import AdminDashboard from './pages/AdminDashboard'
import AdminDataViewer from './pages/AdminDataViewer'
import ExpertRating from './pages/ExpertRating'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/session" element={<TesterSession />} />
        <Route path="/results/:sessionId" element={<ResultsPage />} />
        <Route path="/image/:taskId" element={<ImageDetail />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/data" element={<AdminDataViewer />} />
        <Route path="/expert-rating" element={<ExpertRating />} />
        <Route path="/" element={<Navigate to="/login" replace />} />

      </Routes>
    </BrowserRouter>
  )
}

export default App
