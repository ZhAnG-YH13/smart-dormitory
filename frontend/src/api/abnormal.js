import request from './request'

export function getAbnormals(params) {
  return request({ url: '/api/abnormals', method: 'get', params })
}

export function handleAbnormal(id, data) {
  return request({
    url: `/api/abnormals/${id}/handle`,
    method: 'post',
    data
  })
}

export function closeAbnormal(id) {
  return request({
    url: `/api/abnormals/${id}/close`,
    method: 'post'
  })
}
