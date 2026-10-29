import request from './request'

export function getDashboardStats() {
  return request({ url: '/api/stats/dashboard', method: 'get' })
}
export function getStudentStats() {
  return request({ url: '/api/stats/students', method: 'get' })
}
export function getAccessStats() {
  return request({ url: '/api/stats/access', method: 'get' })
}
export function getClassStats() {
  return request({ url: '/api/stats/classes', method: 'get' })
}
export function getDeviceStats() {
  return request({ url: '/api/stats/devices', method: 'get' })
}
export function getAbnormalStats() {
  return request({ url: '/api/stats/abnormals', method: 'get' })
}
