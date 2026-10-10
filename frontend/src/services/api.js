import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.DEV
    ? 'http://127.0.0.1:5000/api'
    : (import.meta.env.VITE_API_URL || 'https://pcds-library-production.up.railway.app/api'),
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

export default api
