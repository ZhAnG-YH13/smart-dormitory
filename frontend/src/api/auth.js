import request from './request'

export function login(data) {
  return request({
    url: '/api/auth/login',
    method: 'post',
    data
  })
}

export function changePassword(data) {
  return request({
    url: '/api/auth/change-password',
    method: 'post',
    data
  })
}

export function getCurrentUser() {
  return request({
    url: '/api/auth/me',
    method: 'get'
  })
}
