import request from './request'

// 楼栋
export function getBuildings(params) {
  return request({ url: '/api/buildings', method: 'get', params })
}
export function createBuilding(data) {
  return request({ url: '/api/buildings', method: 'post', data })
}
export function updateBuilding(id, data) {
  return request({ url: `/api/buildings/${id}`, method: 'put', data })
}
export function deleteBuilding(id) {
  return request({ url: `/api/buildings/${id}`, method: 'delete' })
}

// 房间
export function getRooms(params) {
  return request({ url: '/api/rooms', method: 'get', params })
}
export function createRoom(data) {
  return request({ url: '/api/rooms', method: 'post', data })
}
export function updateRoom(id, data) {
  return request({ url: `/api/rooms/${id}`, method: 'put', data })
}
export function deleteRoom(id) {
  return request({ url: `/api/rooms/${id}`, method: 'delete' })
}
