import request from './request'

export function getAccessRecords(params) {
  return request({ url: '/api/access/records', method: 'get', params })
}

export function getTodayAccess() {
  return request({ url: '/api/access/today', method: 'get' })
}

export function getPresence() {
  return request({ url: '/api/presence', method: 'get' })
}
