import axios from 'axios'
import router from '../router'
import { useAuthStore } from '../stores/auth'

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

client.interceptors.request.use((req) => {
  const auth = useAuthStore()
  if (auth.token) {
    req.headers = req.headers || {}
    req.headers.Authorization = `Bearer ${auth.token}`
  }
  return req
})

client.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error?.response?.status
    if (status === 401) {
      const auth = useAuthStore()
      auth.logout()
      router.push('/login')
    }
    return Promise.reject(error)
  },
)

export default client
