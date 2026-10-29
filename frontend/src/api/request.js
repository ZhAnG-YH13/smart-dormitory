import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: '',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    const res = response.data
    // 如果后端返回的是标准包装 {code, msg, data}
    if (res && typeof res === 'object' && 'code' in res) {
      if (res.code !== 0 && res.code !== 200) {
        ElMessage.error(res.msg || res.message || '请求失败')
        if (res.code === 401) {
          handleUnauthorized()
        }
        return Promise.reject(new Error(res.msg || '请求失败'))
      }
      return res
    }
    // 否则直接返回 data
    return res
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        handleUnauthorized()
      } else {
        ElMessage.error((data && (data.msg || data.message)) || error.message || '请求失败')
      }
    } else {
      ElMessage.error(error.message || '网络异常')
    }
    return Promise.reject(error)
  }
)

function handleUnauthorized() {
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
  const hash = window.location.hash
  if (!hash.startsWith('#/login')) {
    ElMessage.warning('登录已过期，请重新登录')
    window.location.hash = '#/login'
  }
}

export default service
