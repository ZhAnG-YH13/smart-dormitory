import request from './request'

// 学院
export function getColleges(params) {
  return request({ url: '/api/colleges', method: 'get', params })
}
export function createCollege(data) {
  return request({ url: '/api/colleges', method: 'post', data })
}
export function updateCollege(id, data) {
  return request({ url: `/api/colleges/${id}`, method: 'put', data })
}
export function deleteCollege(id) {
  return request({ url: `/api/colleges/${id}`, method: 'delete' })
}

// 专业
export function getMajors(params) {
  return request({ url: '/api/majors', method: 'get', params })
}
export function createMajor(data) {
  return request({ url: '/api/majors', method: 'post', data })
}
export function updateMajor(id, data) {
  return request({ url: `/api/majors/${id}`, method: 'put', data })
}
export function deleteMajor(id) {
  return request({ url: `/api/majors/${id}`, method: 'delete' })
}

// 年级
export function getGrades(params) {
  return request({ url: '/api/grades', method: 'get', params })
}
export function createGrade(data) {
  return request({ url: '/api/grades', method: 'post', data })
}
export function updateGrade(id, data) {
  return request({ url: `/api/grades/${id}`, method: 'put', data })
}
export function deleteGrade(id) {
  return request({ url: `/api/grades/${id}`, method: 'delete' })
}

// 班级
export function getClasses(params) {
  return request({ url: '/api/classes', method: 'get', params })
}
export function createClass(data) {
  return request({ url: '/api/classes', method: 'post', data })
}
export function updateClass(id, data) {
  return request({ url: `/api/classes/${id}`, method: 'put', data })
}
export function deleteClass(id) {
  return request({ url: `/api/classes/${id}`, method: 'delete' })
}
export function getClassStudents(id) {
  return request({ url: `/api/classes/${id}/students`, method: 'get' })
}
