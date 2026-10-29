import request from './request'

export function registerFace(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/api/face/register',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function getFaceStatus() {
  return request({ url: '/api/face/status', method: 'get' })
}

export function verifyFace(imageBase64) {
  return request({
    url: '/api/face/verify',
    method: 'post',
    data: { image_base64: imageBase64 }
  })
}
