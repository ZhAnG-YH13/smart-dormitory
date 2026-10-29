// 时间格式化
export function formatDateTime(dt) {
  if (!dt) return '-'
  const d = new Date(dt)
  if (isNaN(d.getTime())) return dt
  const pad = (n) => (n < 10 ? '0' + n : n)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

export function formatDate(dt) {
  if (!dt) return '-'
  const d = new Date(dt)
  if (isNaN(d.getTime())) return dt
  const pad = (n) => (n < 10 ? '0' + n : n)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// 相对时间
export function relativeTime(dt) {
  if (!dt) return '-'
  const d = new Date(dt)
  if (isNaN(d.getTime())) return dt
  const diff = Date.now() - d.getTime()
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return '刚刚'
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}分钟前`
  const hour = Math.floor(min / 60)
  if (hour < 24) return `${hour}小时前`
  const day = Math.floor(hour / 24)
  if (day < 30) return `${day}天前`
  return formatDate(dt)
}

// 方向文字
export function directionText(d) {
  if (d === 'IN') return '进入'
  if (d === 'OUT') return '离开'
  return d || '-'
}

// 状态文字
export function statusText(s) {
  const map = {
    online: '在线',
    offline: '离线',
    abnormal: '异常',
    normal: '正常',
    pending: '待处理',
    handling: '处理中',
    resolved: '已处理',
    closed: '已关闭',
    registered: '已注册',
    unregistered: '未注册'
  }
  return map[s] || s || '-'
}

// 角色文字
export function roleText(r) {
  const map = { admin: '管理员', counselor: '辅导员', student: '学生' }
  return map[r] || r || '-'
}

// 严重性文字
export function severityText(s) {
  const map = { low: '低', medium: '中', high: '高', critical: '紧急' }
  return map[s] || s || '-'
}

// 异常类型
export function abnormalTypeText(t) {
  const map = {
    tailgating: '尾随进入',
    loitering: '区域逗留',
    face_mismatch: '人脸不匹配',
    card_invalid: '证件无效',
    device_offline: '设备离线',
    density_high: '密度过高',
    night_out: '夜间未归',
    late_return: '晚归'
  }
  return map[t] || t || '-'
}

// 状态对应的 Element Plus type
export function statusType(s) {
  const map = {
    online: 'success',
    offline: 'danger',
    abnormal: 'warning',
    normal: 'success',
    pending: 'warning',
    handling: '',
    resolved: 'success',
    closed: 'info',
    registered: 'success',
    unregistered: 'info'
  }
  return map[s] || 'info'
}

export function severityType(s) {
  const map = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return map[s] || 'info'
}
