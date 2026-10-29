import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  res => res.data,
  error => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    let msg = '请求失败'
    if (typeof detail === 'string') {
      msg = detail
    } else if (detail && typeof detail === 'object') {
      msg = detail.msg || detail.code || '请求失败'
    } else if (error.message) {
      msg = error.message
    }

    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (router.currentRoute.value.path !== '/login') {
        ElMessage.error('登录已失效，请重新登录')
        router.push('/login')
      }
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default api
