<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">实时门禁 / 模拟通行</h2>
      <div class="header-actions">
        <el-tag type="warning" effect="dark" size="small">演示模式</el-tag>
        <el-button @click="refreshAll"><el-icon><Refresh /></el-icon>刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：摄像头 -->
      <el-col :xs="24" :md="6">
        <div class="page-card panel">
          <div class="section-title">摄像头列表</div>
          <div class="camera-list" v-loading="cameraLoading">
            <div
              v-for="c in cameras"
              :key="c.id"
              class="camera-item"
              :class="{ active: selectedCameraId === c.id }"
              @click="selectCamera(c.id)"
            >
              <div class="camera-item-top">
                <span class="camera-name">{{ c.name }}</span>
                <el-tag :type="statusTagType(c.device_status)" size="small">{{ statusLabel(c.device_status) }}</el-tag>
              </div>
              <div class="camera-item-sub">
                <span>{{ c.camera_code }}</span>
                <span>{{ c.building_name || '未分配宿舍楼' }}</span>
              </div>
            </div>
            <el-empty v-if="!cameraLoading && !cameras.length" description="暂无摄像头" :image-size="70" />
          </div>

          <template v-if="liveCamera">
            <div class="section-title mt-16">设备信息</div>
            <div class="info-row"><span>编号</span><b>{{ liveCamera.camera_code }}</b></div>
            <div class="info-row"><span>位置</span><b>{{ liveCamera.location || '-' }}</b></div>
            <div class="info-row">
              <span>方向</span>
              <el-tag :type="liveCamera.direction === 'IN' ? 'success' : 'warning'" size="small">
                {{ liveCamera.direction === 'IN' ? '进入 IN' : '离开 OUT' }}
              </el-tag>
            </div>
            <div class="info-row">
              <span>状态</span>
              <el-tag :type="statusTagType(liveCamera.device_status)" size="small">
                {{ statusLabel(liveCamera.device_status) }}
              </el-tag>
            </div>
            <div class="info-row"><span>FPS</span><b>{{ liveCamera.fps ?? '-' }}</b></div>
            <div class="info-row">
              <span>心跳</span>
              <el-tag :type="cameraStatus?.heartbeat_ok ? 'success' : 'danger'" size="small">
                {{ cameraStatus?.heartbeat_ok ? '正常' : (cameraStatus ? '超时' : '未知') }}
              </el-tag>
            </div>
            <div class="info-row health-row">
              <span>健康度</span>
              <el-progress
                :percentage="healthPercent(liveCamera.health_score)"
                :stroke-width="9"
                :color="healthColor(liveCamera.health_score)"
                style="flex: 1"
              />
            </div>
            <div class="text-muted" style="margin-top: 8px">
              今日通行 {{ cameraStatus?.today_total ?? '-' }} 次，成功 {{ cameraStatus?.today_success ?? '-' }} 次
            </div>
          </template>
          <el-empty v-else description="请选择左侧摄像头" :image-size="70" />
        </div>
      </el-col>

      <!-- 中部：模拟通行 -->
      <el-col :xs="24" :md="10">
        <div class="page-card panel">
          <div class="section-title">模拟刷脸通行</div>

          <el-form label-width="76px" @submit.prevent>
            <el-form-item label="通行学生">
              <el-select
                v-model="selectedStudentId"
                filterable
                remote
                clearable
                reserve-keyword
                :remote-method="searchStudents"
                :loading="studentLoading"
                placeholder="输入学号 / 姓名远程搜索"
                style="width: 100%"
                @change="onStudentChange"
              >
                <el-option
                  v-for="s in studentOptions"
                  :key="s.id"
                  :label="`${s.student_no} ${s.name}`"
                  :value="s.id"
                />
              </el-select>
            </el-form-item>
          </el-form>

          <div v-if="selectedStudent" class="student-card">
            <div class="student-avatar">{{ (selectedStudent.name || '?').slice(0, 1) }}</div>
            <div class="student-info">
              <div class="student-name">{{ selectedStudent.name }}</div>
              <div class="text-muted">
                {{ selectedStudent.student_no }} · {{ selectedStudent.class_name || '未分班' }}
              </div>
            </div>
            <el-tag :type="faceTagType(selectedStudent.face_status)" size="small">
              {{ faceLabel(selectedStudent.face_status) }}
            </el-tag>
          </div>
          <el-empty v-else description="请先搜索并选择学生" :image-size="60" />

          <div class="similarity-box">
            <div class="similarity-head">
              <span>人脸相似度</span>
              <b>{{ similarity.toFixed(2) }}</b>
            </div>
            <el-slider v-model="similarity" :min="0" :max="1" :step="0.01" :marks="{ 0.6: '阈值 0.60' }" />
            <div class="text-muted">低于阈值 0.60 将判定验证失败</div>
          </div>

          <div class="action-row">
            <el-button
              type="primary"
              size="large"
              :loading="simulating"
              :disabled="!selectedCameraId || !selectedStudentId"
              @click="doSimulate(similarity)"
            >
              <el-icon><VideoCamera /></el-icon>模拟刷脸通行
            </el-button>
            <el-button
              type="danger"
              plain
              size="large"
              :loading="simulating"
              :disabled="!selectedCameraId"
              @click="simulateUnregistered"
            >
              模拟未注册学生
            </el-button>
          </div>

          <div v-if="result" class="result-panel" :class="result.verify_result === 'success' ? 'ok' : 'bad'">
            <div class="result-icon">
              <el-icon :size="46">
                <CircleCheckFilled v-if="result.verify_result === 'success'" />
                <CircleCloseFilled v-else />
              </el-icon>
            </div>
            <div class="result-title">{{ result.verify_result === 'success' ? '通行成功' : '验证失败' }}</div>
            <div class="result-desc">
              {{ result.student_name }} ·
              {{ result.direction === 'IN' ? '进入' : '离开' }} ·
              相似度 {{ Number(result.similarity).toFixed(2) }}
            </div>
            <div class="result-tags">
              <el-tag :type="result.direction === 'IN' ? 'success' : 'warning'">
                {{ result.direction === 'IN' ? '进入' : '离开' }}
              </el-tag>
              <el-tag :type="result.is_present ? 'success' : 'info'">
                {{ result.is_present ? '在寝' : '不在寝' }}
              </el-tag>
              <el-tag v-if="result.verify_result === 'success'" type="success">在寝状态已更新</el-tag>
            </div>
            <div v-if="result.verify_result !== 'success'" class="fail-tip">
              人脸验证失败，请调整姿态重新尝试
            </div>
            <div class="text-muted" style="margin-top: 6px">门禁记录 ID：{{ result.access_record_id }}</div>
          </div>
          <div v-else class="result-placeholder">
            <el-icon :size="36"><Camera /></el-icon>
            <div class="text-muted">选择摄像头与学生后，点击「模拟刷脸通行」查看识别结果</div>
          </div>
        </div>
      </el-col>

      <!-- 右侧：最近记录 -->
      <el-col :xs="24" :md="8">
        <div class="page-card panel">
          <div class="section-title">
            <span>最近门禁记录</span>
            <el-button link type="primary" @click="loadRecords"><el-icon><Refresh /></el-icon>刷新</el-button>
          </div>
          <div v-loading="recordsLoading" class="record-list">
            <div v-for="r in records" :key="r.id" class="record-item">
              <div class="record-top">
                <span class="record-name">{{ r.student_name || '未知' }}</span>
                <el-tag :type="r.direction === 'IN' ? 'success' : 'warning'" size="small">
                  {{ r.direction === 'IN' ? '进入' : '离开' }}
                </el-tag>
                <el-tag :type="r.verify_result === 'success' ? 'success' : 'danger'" size="small">
                  {{ r.verify_result === 'success' ? '成功' : '失败' }}
                </el-tag>
              </div>
              <div class="record-sub">
                <span>{{ r.student_no }}</span>
                <span>{{ r.camera_code }}</span>
                <span>{{ formatTime(r.occurred_at) }}</span>
              </div>
            </div>
            <el-empty v-if="!recordsLoading && !records.length" description="暂无门禁记录" :image-size="70" />
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const cameras = ref([])
const cameraLoading = ref(false)
const selectedCameraId = ref(null)
const cameraStatus = ref(null)
const records = ref([])
const recordsLoading = ref(false)

const studentOptions = ref([])
const studentLoading = ref(false)
const selectedStudentId = ref(null)
const selectedStudent = ref(null)

const similarity = ref(0.85)
const simulating = ref(false)
const result = ref(null)

let statusTimer = null
let recordsTimer = null

const selectedCamera = computed(() => cameras.value.find(c => c.id === selectedCameraId.value) || null)
const liveCamera = computed(() => cameraStatus.value?.camera || selectedCamera.value)

const statusMap = {
  online: { label: '在线', type: 'success' },
  offline: { label: '离线', type: 'danger' },
  error: { label: '异常', type: 'danger' },
  maintenance: { label: '维护', type: 'info' }
}
const faceMap = {
  registered: { label: '已注册人脸', type: 'success' },
  unregistered: { label: '未注册人脸', type: 'info' },
  registering: { label: '注册中', type: 'warning' },
  failed: { label: '注册失败', type: 'danger' },
  cancelled: { label: '已注销', type: 'info' }
}

function statusLabel(v) {
  return statusMap[v]?.label || v || '-'
}
function statusTagType(v) {
  return statusMap[v]?.type || 'info'
}
function faceLabel(v) {
  return faceMap[v]?.label || '未注册人脸'
}
function faceTagType(v) {
  return faceMap[v]?.type || 'info'
}
function healthPercent(v) {
  const n = Number(v)
  if (Number.isNaN(n)) return 0
  return Math.max(0, Math.min(100, Math.round(n)))
}
function healthColor(v) {
  const n = Number(v) || 0
  if (n >= 80) return '#67c23a'
  if (n >= 60) return '#e6a23c'
  return '#f56c6c'
}
function formatTime(v) {
  if (!v) return '-'
  return String(v).replace('T', ' ').slice(0, 19)
}

async function loadCameras() {
  cameraLoading.value = true
  try {
    const res = await api.get('/cameras', { params: { limit: 100 } })
    cameras.value = res.items || []
    if (!selectedCameraId.value && cameras.value.length) {
      selectCamera(cameras.value[0].id)
    }
  } catch (e) {
    cameras.value = []
  } finally {
    cameraLoading.value = false
  }
}

async function loadCameraStatus() {
  if (!selectedCameraId.value) return
  try {
    const res = await api.get(`/cameras/${selectedCameraId.value}/status`)
    cameraStatus.value = res
    if (res?.camera) {
      const idx = cameras.value.findIndex(c => c.id === res.camera.id)
      if (idx >= 0) Object.assign(cameras.value[idx], res.camera)
    }
  } catch (e) {
    /* 忽略轮询错误 */
  }
}

function selectCamera(id) {
  selectedCameraId.value = id
  cameraStatus.value = null
  loadCameraStatus()
}

async function searchStudents(keyword) {
  if (!keyword) {
    studentOptions.value = []
    return
  }
  studentLoading.value = true
  try {
    const res = await api.get('/students', { params: { keyword, limit: 20 } })
    studentOptions.value = res.items || []
  } catch (e) {
    studentOptions.value = []
  } finally {
    studentLoading.value = false
  }
}

function onStudentChange(id) {
  selectedStudent.value = studentOptions.value.find(s => s.id === id) || null
}

async function doSimulate(sim) {
  if (!selectedCameraId.value) {
    ElMessage.warning('请先选择摄像头')
    return
  }
  if (!selectedStudentId.value) {
    ElMessage.warning('请先选择学生')
    return
  }
  simulating.value = true
  try {
    const res = await api.post(`/cameras/${selectedCameraId.value}/simulate`, {
      student_id: selectedStudentId.value,
      similarity: sim
    })
    result.value = res
    if (res.verify_result === 'success') {
      ElMessage.success(`通行成功：${res.student_name}`)
    } else {
      ElMessage.warning('人脸验证失败')
    }
    loadRecords()
    loadCameraStatus()
  } catch (e) {
    /* 错误提示由拦截器处理 */
  } finally {
    simulating.value = false
  }
}

async function simulateUnregistered() {
  if (!selectedCameraId.value) {
    ElMessage.warning('请先选择摄像头')
    return
  }
  try {
    const res = await api.get('/students', { params: { face_status: 'unregistered', limit: 20 } })
    const items = res.items || []
    if (!items.length) {
      ElMessage.warning('暂无未注册人脸的学生，无法模拟')
      return
    }
    const stu = items[0]
    studentOptions.value = [stu, ...studentOptions.value.filter(s => s.id !== stu.id)]
    selectedStudentId.value = stu.id
    selectedStudent.value = stu
    similarity.value = 0.3
    await doSimulate(0.3)
  } catch (e) {
    /* 忽略 */
  }
}

async function loadRecords() {
  recordsLoading.value = true
  try {
    const res = await api.get('/access/records', { params: { limit: 10 } })
    records.value = res.items || []
  } catch (e) {
    records.value = []
  } finally {
    recordsLoading.value = false
  }
}

function refreshAll() {
  loadCameras()
  loadRecords()
  loadCameraStatus()
}

onMounted(() => {
  loadCameras()
  loadRecords()
  statusTimer = setInterval(loadCameraStatus, 5000)
  recordsTimer = setInterval(loadRecords, 10000)
})

onUnmounted(() => {
  if (statusTimer) clearInterval(statusTimer)
  if (recordsTimer) clearInterval(recordsTimer)
  statusTimer = null
  recordsTimer = null
})
</script>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel {
  min-height: 580px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.camera-list {
  max-height: 300px;
  overflow-y: auto;
  padding-right: 4px;
}

.camera-item {
  padding: 10px 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.camera-item:hover {
  border-color: #409eff;
}

.camera-item.active {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 0 0 1px #409eff inset;
}

.camera-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.camera-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.camera-item-sub {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 0;
  font-size: 13px;
  color: #606266;
  gap: 10px;
}

.info-row b {
  color: #303133;
  font-weight: 500;
  text-align: right;
  word-break: break-all;
}

.health-row {
  gap: 12px;
}

.student-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  background: #fafcff;
  margin-bottom: 16px;
}

.student-avatar {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff, #1e3c72);
  color: #fff;
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.student-info {
  flex: 1;
  min-width: 0;
}

.student-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 2px;
}

.similarity-box {
  padding: 14px 16px 6px;
  border-radius: 10px;
  background: #f5f7fa;
  margin-bottom: 16px;
}

.similarity-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}

.similarity-head b {
  font-size: 18px;
  color: #409eff;
}

.action-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-row .el-button {
  flex: 1;
  margin-left: 0;
}

.result-panel {
  margin-top: 16px;
  text-align: center;
  padding: 18px 16px;
  border-radius: 12px;
  border: 1px solid #dcdfe6;
  background: #fafafa;
}

.result-panel.ok {
  border-color: #b3e19d;
  background: #f0f9eb;
}

.result-panel.bad {
  border-color: #fbc4c4;
  background: #fef0f0;
}

.result-panel.ok .result-icon,
.result-panel.ok .result-title {
  color: #67c23a;
}

.result-panel.bad .result-icon,
.result-panel.bad .result-title {
  color: #f56c6c;
}

.result-title {
  font-size: 24px;
  font-weight: 700;
  margin: 4px 0 6px;
}

.result-desc {
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
}

.result-tags {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.fail-tip {
  margin-top: 10px;
  color: #f56c6c;
  font-size: 14px;
  font-weight: 600;
}

.result-placeholder {
  margin-top: 16px;
  padding: 30px 16px;
  border: 1px dashed #dcdfe6;
  border-radius: 12px;
  text-align: center;
  color: #909399;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.record-list {
  max-height: 520px;
  overflow-y: auto;
}

.record-item {
  padding: 10px 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 8px;
}

.record-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.record-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.record-sub {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 5px;
  font-size: 12px;
  color: #909399;
}
</style>
