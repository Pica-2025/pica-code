import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.clear()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const login = (username, password) =>
  api.post('/auth/login', { username, password })

export const logout = () =>
  api.post('/auth/logout')

export const startSession = () =>
  api.post('/sessions/start')

export const getSessionDetail = (sessionId) =>
  api.get(`/sessions/${sessionId}`)

export const getSessionProgress = (sessionId) =>
  api.get(`/sessions/${sessionId}/progress`)

export const finishSession = (sessionId) =>
  api.post(`/sessions/${sessionId}/finish`)

export const submitTask = (taskId, data) =>
  api.post(`/tasks/${taskId}/submit`, data)

export const getTaskStatus = (taskId) =>
  api.get(`/tasks/${taskId}/status`)

export const getTaskDetail = (taskId) =>
  api.get(`/tasks/${taskId}/detail`)

export const rateVersion = (versionId, data) =>
  api.post(`/versions/${versionId}/rate`, data)

export const finalizeVersion = (versionId) =>
  api.post(`/versions/${versionId}/finalize`)

export const getVersionDetail = (versionId) =>
  api.get(`/versions/${versionId}/detail`)

export const getAdminStats = () =>
  api.get('/admin/stats')

export const getAllUsers = () =>
  api.get('/admin/users')

export const getRatingDimensions = () =>
  api.get('/rating-dimensions')

export const autoScoreVersion = (versionId) =>
  api.post(`/versions/${versionId}/auto-score`)

export const getAdminUsersWithSessions = () =>
  api.get('/admin/data/users')

export const getAdminSessionTasks = (sessionId) =>
  api.get(`/admin/data/sessions/${sessionId}/tasks`)

export const getAdminTaskAllVersions = (taskId) =>
  api.get(`/admin/data/tasks/${taskId}/all-versions`)

export const getAdminDetailedStats = () =>
  api.get('/admin/data/statistics')

export const updateAdminDifficulty = (taskId, difficultyRating) => {
  return api.put(`/admin/data/tasks/${taskId}/admin-difficulty`, null, {
    params: { difficulty_rating: difficultyRating }
  })
}

export default api
