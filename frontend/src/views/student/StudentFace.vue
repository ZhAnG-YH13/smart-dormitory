<template>
  <div>
    <div class="page-card">
      <div class="page-header">
        <h2 class="page-title">人脸注册</h2>
        <div>
          <el-button @click="loadStatus"><el-icon><Refresh /></el-icon>刷新状态</el-button>
          <el-button v-if="isRegistered" type="warning" plain @click="startReRegister">
            <el-icon><RefreshRight /></el-icon>重新注册
          </el-button>
          <el-button v-if="isRegistered" type="danger" plain :loading="cancelling" @click="cancelFace">
            注销人脸
          </el-button>
        </div>
      </div>

      <div class="face-stats">
        <div class="face-stat">
          <div class="label">人脸状态</div>
          <el-tag :type="faceTag.type" size="large">{{ faceTag.text }}</el-tag>
        </div>
        <div class="face-stat">
          <div class="label">质量分</div>
          <div class="value">{{ scoreText(status.quality_score) }}</div>
        </div>
        <div class="face-stat">
          <div class="label">验证次数 / 成功次数</div>
          <div class="value">{{ status.verify_count ?? 0 }} / {{ status.verify_success_count ?? 0 }}</div>
        </div>
        <div class="face-stat">
          <div class="label">注册时间</div>
          <div class="value small">{{ formatTime(status.registered_at) }}</div>
        </div>
      </div>
    </div>

    <div class="page-card mt-16">
      <el-alert
        class="result-alert"
        v-if="result"
        :type="result.type"
        :title="result.message"
        show-icon
        @close="result = null"
      />

      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="采集要求：正脸面对镜头、光线充足均匀、画面中仅本人、图像清晰不模糊"
      />

      <el-tabs v-model="activeTab" class="mt-16" @tab-change="onTabChange">
        <el-tab-pane label="上传照片" name="upload">
          <div class="upload-area">
            <el-upload
              drag
              :auto-upload="false"
              :show-file-list="false"
              accept="image/*"
              :on-change="onFileChange"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">将照片拖到此处，或 <em>点击选择</em></div>
              <template #tip>
                <div class="el-upload__tip">支持 JPG / PNG 格式，大小不超过 10MB</div>
              </template>
            </el-upload>

            <div v-if="previewUrl" class="preview-box">
              <div class="text-muted">照片预览</div>
              <img :src="previewUrl" alt="人脸照片预览" />
            </div>

            <div class="actions">
              <el-button
                type="primary"
                :loading="registering"
                :disabled="!selectedFile"
                @click="registerByUpload"
              >
                <el-icon><Upload /></el-icon>上传并注册
              </el-button>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="摄像头采集" name="camera">
          <div class="camera-area">
            <div class="video-box">
              <video ref="videoRef" autoplay playsinline muted></video>
              <div v-if="!cameraOn" class="video-placeholder">摄像头未开启</div>
            </div>

            <div class="actions">
              <el-button v-if="!cameraOn" type="primary" @click="openCamera">
                <el-icon><VideoCamera /></el-icon>开启摄像头
              </el-button>
              <template v-else>
                <el-button type="primary" :loading="registering" @click="captureAndRegister">
                  <el-icon><Camera /></el-icon>拍照并注册
                </el-button>
                <el-button @click="stopCamera">关闭摄像头</el-button>
              </template>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const status = ref({})
const activeTab = ref('upload')
const registering = ref(false)
const cancelling = ref(false)
const result = ref(null)

const selectedFile = ref(null)
const previewUrl = ref('')
const videoRef = ref(null)
const stream = ref(null)
const cameraOn = ref(false)

const FACE_MAP = {
  registered: { text: '已注册', type: 'success' },
  unregistered: { text: '未注册', type: 'info' },
  registering: { text: '注册中', type: 'warning' },
  failed: { text: '注册失败', type: 'danger' },
  cancelled: { text: '已注销', type: 'info' }
}

const reasonMap = {
  NO_FACE_DETECTED: '未检测到人脸，请重新上传',
  MULTIPLE_FACES: '检测到多张人脸，请保证图片中只有本人',
  FACE_TOO_BLUR: '当前照片过于模糊，请重新拍摄',
  FACE_TOO_DARK: '图像过暗，请在光线充足处拍摄',
  FACE_TOO_BRIGHT: '图像过曝，请避免强光直射',
  FACE_TOO_SMALL: '人脸过小，请靠近摄像头'
}

const faceTag = computed(() => {
  const s = status.value.face_status || 'unregistered'
  return FACE_MAP[s] || { text: s, type: 'info' }
})

const isRegistered = computed(() => status.value.face_status === 'registered')

function scoreText(v) {
  const n = Number(v)
  if (!Number.isFinite(n) || v === null || v === undefined) return '-'
  return n.toFixed(1)
}

function formatTime(t) {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 19)
}

async function loadStatus() {
  try {
    status.value = (await api.get('/face/status')) || {}
  } catch (e) {
    status.value = {}
  }
}

function clearSelected() {
  selectedFile.value = null
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
}

function onFileChange(uploadFile) {
  const raw = uploadFile?.raw
  if (!raw) return
  if (raw.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过 10MB')
    return
  }
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  selectedFile.value = raw
  previewUrl.value = URL.createObjectURL(raw)
}

async function registerByUpload() {
  if (!selectedFile.value) return ElMessage.warning('请先选择一张照片')
  const fd = new FormData()
  fd.append('file', selectedFile.value)
  await doRegister(fd)
}

async function doRegister(fd) {
  registering.value = true
  result.value = null
  try {
    const res = await api.post('/face/register', fd)
    if (res?.success) {
      result.value = { type: 'success', message: `注册成功，质量分 ${scoreText(res.quality_score)}` }
      ElMessage.success('人脸注册成功')
    } else {
      const message = reasonMap[res?.reason] || res?.detail || res?.msg || '注册失败，请重新采集'
      result.value = { type: 'error', message }
      ElMessage.error(message)
    }
    await loadStatus()
  } catch (e) {
    // 错误提示已由拦截器处理
  } finally {
    registering.value = false
  }
}

async function openCamera() {
  try {
    const s = await navigator.mediaDevices.getUserMedia({ video: true })
    stream.value = s
    cameraOn.value = true
    await nextTick()
    if (videoRef.value) {
      videoRef.value.srcObject = s
      await videoRef.value.play().catch(() => {})
    }
  } catch (e) {
    cameraOn.value = false
    ElMessage.error('无法打开摄像头，请检查设备连接与浏览器权限')
  }
}

function stopCamera() {
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
    stream.value = null
  }
  if (videoRef.value) {
    videoRef.value.srcObject = null
  }
  cameraOn.value = false
}

async function captureAndRegister() {
  const video = videoRef.value
  if (!video || !stream.value) return ElMessage.warning('请先开启摄像头')
  const width = video.videoWidth
  const height = video.videoHeight
  if (!width || !height) return ElMessage.warning('摄像头尚未就绪，请稍后再试')

  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  canvas.getContext('2d').drawImage(video, 0, 0, width, height)

  const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.92))
  if (!blob) return ElMessage.error('拍照失败，请重试')

  const fd = new FormData()
  fd.append('file', blob, `camera_${Date.now()}.jpg`)
  await doRegister(fd)
}

function startReRegister() {
  activeTab.value = 'upload'
  clearSelected()
  result.value = null
  ElMessage.info('请重新采集人脸照片后提交注册')
}

function cancelFace() {
  ElMessageBox.confirm('注销后人脸数据将被清除，需重新注册才能使用人脸门禁，确定继续吗？', '注销人脸', {
    type: 'warning',
    confirmButtonText: '确定注销',
    cancelButtonText: '取消'
  }).then(async () => {
    cancelling.value = true
    try {
      await api.delete('/face/cancel')
      ElMessage.success('人脸已注销')
      result.value = null
      clearSelected()
      await loadStatus()
    } catch (e) {
      // 错误提示已由拦截器处理
    } finally {
      cancelling.value = false
    }
  }).catch(() => {})
}

function onTabChange(name) {
  if (name !== 'camera') stopCamera()
}

onUnmounted(() => {
  stopCamera()
  clearSelected()
})

loadStatus()
</script>

<style scoped>
.face-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
}

.face-stat {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 14px 16px;
  min-height: 82px;
}

.face-stat .label {
  font-size: 13px;
  color: #88909b;
  margin-bottom: 10px;
}

.face-stat .value {
  font-size: 22px;
  font-weight: 600;
  color: #1f2d3d;
}

.face-stat .value.small {
  font-size: 14px;
  font-weight: 400;
  padding-top: 6px;
}

.result-alert {
  margin-bottom: 12px;
}

.upload-area {
  max-width: 620px;
}

.preview-box {
  margin-top: 16px;
}

.preview-box img {
  max-width: 100%;
  max-height: 260px;
  margin-top: 8px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
}

.camera-area {
  max-width: 620px;
}

.video-box {
  position: relative;
  width: 100%;
  height: 320px;
  background: #1f2d3d;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-box video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  font-size: 14px;
  background: #1f2d3d;
}
</style>
