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

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = error.config?.url || ''
    const isSignInRequest = /^\/auth\/(login|google)(?:[/?]|$)/.test(requestUrl)

    if (error.response?.status === 401 && !isSignInRequest && error.config?.headers?.Authorization) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      sessionStorage.setItem('pcds_session_expired', 'true')
      window.location.replace('/?session=expired')
    }

    return Promise.reject(error)
  },
)

export default api
