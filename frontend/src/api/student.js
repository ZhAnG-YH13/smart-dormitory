import request from './request'

export function getStudents(params) {
  return request({ url: '/api/students', method: 'get', params })
}

export function getStudent(id) {
  return request({ url: `/api/students/${id}`, method: 'get' })
}

export function createStudent(data) {
  return request({ url: '/api/students', method: 'post', data })
}

export function updateStudent(id, data) {
  return request({ url: `/api/students/${id}`, method: 'put', data })
}

export function deleteStudent(id) {
  return request({ url: `/api/students/${id}`, method: 'delete' })
}

export function importStudents(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/api/students/import',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function createStudentAccounts(studentIds) {
  return request({
    url: '/api/students/create-accounts',
    method: 'post',
    data: { student_ids: studentIds }
  })
}

export function resetStudentPassword(id) {
  return request({
    url: `/api/students/${id}/reset-password`,
    method: 'post'
  })
}
