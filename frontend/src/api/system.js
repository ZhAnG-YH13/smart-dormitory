import request from './request'

export function getSystemInfo() {
  return request({ url: '/api/system/info', method: 'get' })
}

export function getOperationLogs(params) {
  return request({ url: '/api/logs', method: 'get', params })
}

// 用户管理
export function getUsers(params) {
  return request({ url: '/api/users', method: 'get', params })
}
export function createUser(data) {
  return request({ url: '/api/users', method: 'post', data })
}
export function updateUser(id, data) {
  return request({ url: `/api/users/${id}`, method: 'put', data })
}
export function deleteUser(id) {
  return request({ url: `/api/users/${id}`, method: 'delete' })
}
