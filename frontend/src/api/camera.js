import request from './request'

export function getCameras(params) {
  return request({ url: '/api/cameras', method: 'get', params })
}
export function getCamera(id) {
  return request({ url: `/api/cameras/${id}`, method: 'get' })
}
export function createCamera(data) {
  return request({ url: '/api/cameras', method: 'post', data })
}
export function updateCamera(id, data) {
  return request({ url: `/api/cameras/${id}`, method: 'put', data })
}
export function deleteCamera(id) {
  return request({ url: `/api/cameras/${id}`, method: 'delete' })
}
export function simulateCamera(id, direction = 'IN') {
  return request({
    url: `/api/cameras/${id}/simulate`,
    method: 'post',
    data: { direction }
  })
}
