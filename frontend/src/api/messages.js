import request from './request'

export function getMessages(params) {
  return request({ url: '/api/messages', method: 'get', params })
}

export function getUnreadCount() {
  return request({ url: '/api/messages/unread-count', method: 'get' })
}

export function markMessageRead(id) {
  return request({ url: `/api/messages/${id}/read`, method: 'post' })
}
