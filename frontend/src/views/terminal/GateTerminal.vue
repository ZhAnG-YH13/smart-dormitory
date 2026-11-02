<template>
  <div class="terminal">
    <div class="topbar">
      <div class="brand">
        <div class="logo">🏛️</div>
        <div>
          <div class="title">智慧宿舍人脸门禁终端</div>
          <div class="subtitle">实时刷脸 · 自动开门 · 在寝联动</div>
        </div>
      </div>
      <div class="controls">
        <el-select
          v-model="cameraCode"
          placeholder="选择门禁设备"
          size="large"
          @change="onCameraChange"
        >
          <el-option
            v-for="c in cameras"
            :key="c.camera_code"
            :label="`${c.camera_code} · ${c.name}`"
            :value="c.camera_code"
          >
            <span>{{ c.camera_code }} · {{ c.name }}</span>
            <span class="opt-tag">{{ c.direction === 'IN' ? '入口' : '出口' }}</span>
          </el-option>
        </el-select>
        <span class="live-pill" :class="cameraReady ? 'ok' : (cameraError ? 'err' : '')">
          <i class="dot"></i>
          {{ cameraReady ? '摄像头常开 · 实时识别中' : (cameraError ? '摄像头异常 · 自动重试中' : '摄像头启动中…') }}
        </span>
      </div>
    </div>

    <div class="stage">
      <div class="video-wrap">
        <video ref="videoRef" autoplay playsinline muted class="video" :class="{ mirrored: true }"></video>
        <div class="scan-frame"></div>
        <div v-if="!cameraReady" class="video-placeholder">
          <el-icon :size="46"><Camera /></el-icon>
          <div>{{ cameraError || '正在开启摄像头…' }}</div>
          <div class="hint">终端摄像头由系统自动开启并保持常开，无需人工启停</div>
        </div>

        <transition name="fade">
          <div v-if="overlay" class="overlay" :class="overlay.type">
            <el-icon :size="72">
              <CircleCheckFilled v-if="overlay.type === 'success'" />
              <CircleCloseFilled v-else />
            </el-icon>
            <div class="overlay-title">{{ overlay.title }}</div>
            <div class="overlay-sub">{{ overlay.sub }}</div>
          </div>
        </transition>

        <div class="badge" v-if="currentCamera">
          {{ currentCamera.building }} · {{ currentCamera.name }}
          <el-tag size="small" :type="currentCamera.direction === 'IN' ? 'success' : 'warning'">
            {{ currentCamera.direction === 'IN' ? '进入' : '离开' }}
          </el-tag>
        </div>
      </div>

      <div class="side">
        <div class="stat-row">
          <div class="stat">
            <div class="label">识别次数</div>
            <div class="value">{{ stats.total }}</div>
          </div>
          <div class="stat">
            <div class="label">成功开门</div>
            <div class="value ok">{{ stats.success }}</div>
          </div>
          <div class="stat">
            <div class="label">最近耗时</div>
            <div class="value small">{{ stats.ms ? stats.ms + ' ms' : '-' }}</div>
          </div>
        </div>

        <div class="panel-title">最近通行</div>
        <div class="records">
          <div v-if="!records.length" class="empty">暂无记录</div>
          <div v-for="r in records" :key="r.key" class="record" :class="r.success ? 'ok' : 'fail'">
            <div class="rec-main">
              <span class="name">{{ r.name }}</span>
              <span class="sim">相似度 {{ r.similarity }}</span>
            </div>
            <div class="rec-sub">
              {{ r.studentNo }} · {{ r.direction }} · {{ r.time }}
              <span v-if="r.duplicate" class="dup">重复</span>
            </div>
          </div>
        </div>

        <div class="tip">
          终端摄像头常开，无需人工启停；支持同一画面多人同时识别，通过者逐一开门并写入门禁记录。
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const cameras = ref([])
const cameraCode = ref('')
const cameraReady = ref(false)
const cameraError = ref('')
const overlay = ref(null)
const records = ref([])
const stats = ref({ total: 0, success: 0, ms: 0 })

const videoRef = ref(null)
let stream = null
let timer = null
let retryTimer = null
let inFlight = false
let overlayTimer = null
let audioCtx = null
let destroyed = false

const currentCamera = computed(() => cameras.value.find(c => c.camera_code === cameraCode.value))

function loadCameras() {
  return api.get('/face/terminal-cameras').then(res => {
    cameras.value = res.items || []
    const preferred = new URLSearchParams(location.search).get('camera')
    const saved = localStorage.getItem('terminal_camera')
    const code = preferred || saved || (cameras.value[0] && cameras.value[0].camera_code)
    if (code && cameras.value.some(c => c.camera_code === code)) {
      cameraCode.value = code
    } else if (cameras.value.length) {
      cameraCode.value = cameras.value[0].camera_code
    }
  })
}

function onCameraChange(code) {
  localStorage.setItem('terminal_camera', code)
}

// 摄像头由终端自动开启并保持常开，页面上不提供启停入口
async function startCamera() {
  if (destroyed || stream) return
  cameraError.value = ''
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
      audio: false
    })
    const track = stream.getVideoTracks()[0]
    if (track) track.onended = () => { onCameraLost('摄像头被断开，正在自动重连…') }
    videoRef.value.srcObject = stream
    await videoRef.value.play()
    cameraReady.value = true
    if (!timer) timer = setInterval(recognizeOnce, 1800)
  } catch (e) {
    cameraError.value = insecureContext
      ? '当前地址不是 HTTPS，浏览器禁止调用摄像头，请使用 HTTPS 地址访问'
      : `摄像头启动失败：${e.name === 'NotAllowedError' ? '未授权摄像头权限' : e.message}`
    releaseCamera()
    scheduleRetry()
  }
}

function onCameraLost(msg) {
  cameraError.value = msg
  cameraReady.value = false
  releaseCamera()
  scheduleRetry()
}

function scheduleRetry() {
  if (destroyed) return
  if (retryTimer) clearTimeout(retryTimer)
  retryTimer = setTimeout(() => { if (!destroyed && !stream) startCamera() }, 4000)
}

function releaseCamera() {
  cameraReady.value = false
  if (timer) { clearInterval(timer); timer = null }
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null }
  if (videoRef.value) videoRef.value.srcObject = null
}

async function recognizeOnce() {
  if (inFlight || !cameraReady.value || !cameraCode.value) return
  inFlight = true
  const started = performance.now()
  try {
    const blob = await captureFrame()
    if (!blob) return
    const fd = new FormData()
    fd.append('file', blob, 'frame.jpg')
    fd.append('camera_code', cameraCode.value)
    const res = await api.post('/face/terminal-verify', fd)
    stats.value.total += 1
    stats.value.ms = res.recognition_ms ?? Math.round(performance.now() - started)

    // 画面中可能有多人，后端返回 matches 数组；命中者逐一开门
    const list = res.matches && res.matches.length
      ? res.matches
      : (res.student ? [{ student: res.student, similarity: res.similarity, direction: res.direction, cooldown: res.cooldown }] : [])
    const fresh = list.filter(m => !m.cooldown)
    const peopleTag = res.face_count > 1 ? ` · 画面 ${res.face_count} 人` : ''

    if (res.success && fresh.length) {
      stats.value.success += fresh.length
      const names = fresh.map(m => m.student?.name).filter(Boolean).join('、')
      const detail = fresh.map(m => `${m.student?.name || ''} ${Number(m.similarity || 0).toFixed(4)}`).join(' · ')
      showOverlay(
        'success',
        `开门成功：${names}`,
        `${detail} · ${fresh[0].direction === 'IN' ? '进入' : '离开'}宿舍${peopleTag}`
      )
      beep(true)
      fresh.forEach(m => pushRecord({
        name: m.student?.name || '',
        studentNo: m.student?.student_no || '',
        similarity: Number(m.similarity || 0).toFixed(4),
        direction: m.direction,
        duplicate: Boolean(m.duplicate)
      }))
    } else if (!res.success && !res.cooldown) {
      showOverlay(
        'fail',
        res.reason === 'NO_FACE_DETECTED' ? '未检测到人脸' : '识别失败',
        res.detail || `相似度 ${Number(res.similarity || 0).toFixed(4)} 低于阈值 ${res.threshold ?? 0.6}`
      )
      beep(false)
      pushRecord({
        name: '未知人员',
        studentNo: '-',
        similarity: Number(res.similarity || 0).toFixed(4),
        direction: currentCamera.value?.direction || 'IN',
        duplicate: false
      })
    }
  } catch (e) {
    // 网络或后端异常时静默跳过本次
  } finally {
    inFlight = false
  }
}

function captureFrame() {
  const video = videoRef.value
  if (!video || !video.videoWidth) return Promise.resolve(null)
  // 限制上传分辨率, 降低识别耗时
  const maxW = 480
  const scale = Math.min(1, maxW / video.videoWidth)
  const w = Math.round(video.videoWidth * scale)
  const h = Math.round(video.videoHeight * scale)
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  ctx.translate(w, 0)
  ctx.scale(-1, 1)
  ctx.drawImage(video, 0, 0, w, h)
  return new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.85))
}

function pushRecord(r) {
  records.value.unshift({
    ...r,
    key: Date.now() + Math.random(),
    time: new Date().toLocaleTimeString()
  })
  if (records.value.length > 8) records.value.pop()
}

function showOverlay(type, title, sub) {
  overlay.value = { type, title, sub }
  if (overlayTimer) clearTimeout(overlayTimer)
  overlayTimer = setTimeout(() => { overlay.value = null }, type === 'success' ? 4000 : 2200)
}

function beep(ok) {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = audioCtx.createOscillator()
    const gain = audioCtx.createGain()
    osc.connect(gain)
    gain.connect(audioCtx.destination)
    osc.frequency.value = ok ? 880 : 220
    gain.gain.value = 0.08
    osc.start()
    setTimeout(() => { osc.stop(); osc.disconnect() }, ok ? 220 : 400)
  } catch (e) { /* 忽略音频异常 */ }
}

const insecureContext = !window.isSecureContext

onMounted(async () => {
  try {
    await loadCameras()
  } catch (e) {
    // 设备列表失败时仍尝试开启摄像头
  }
  startCamera()
})

onUnmounted(() => {
  destroyed = true
  if (retryTimer) clearTimeout(retryTimer)
  releaseCamera()
  if (overlayTimer) clearTimeout(overlayTimer)
})
</script>

<style scoped>
.terminal {
  min-height: 100vh;
  padding: 18px 22px 26px;
  background: radial-gradient(1000px 500px at 15% -10%, #17324f 0%, transparent 60%),
              radial-gradient(800px 460px at 95% 5%, #123a4a 0%, transparent 55%),
              linear-gradient(160deg, #0a1421 0%, #0d1b2b 55%, #081018 100%);
  color: #e7eef8;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; flex-wrap: wrap;
}
.brand { display: flex; align-items: center; gap: 14px; }
.logo {
  width: 50px; height: 50px; border-radius: 14px; font-size: 24px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #409eff, #2b6fd6);
  box-shadow: 0 10px 26px rgba(64, 158, 255, .35);
}
.title { font-size: 20px; font-weight: 700; letter-spacing: .5px; }
.subtitle { font-size: 12px; color: #7e96b1; margin-top: 4px; }
.controls { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.opt-tag { float: right; color: #9aa; font-size: 12px; }
.live-pill {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 14px; border-radius: 999px; font-size: 12.5px;
  background: rgba(255, 255, 255, .05); border: 1px solid rgba(255, 255, 255, .12);
  color: #9fb4c9; white-space: nowrap;
}
.live-pill .dot { width: 7px; height: 7px; border-radius: 50%; background: #ffb454; }
.live-pill.ok { color: #3ddc84; border-color: rgba(61, 220, 132, .35); }
.live-pill.ok .dot { background: #3ddc84; box-shadow: 0 0 8px rgba(61, 220, 132, .8); }
.live-pill.err { color: #ff6b6b; border-color: rgba(255, 107, 107, .35); }
.live-pill.err .dot { background: #ff6b6b; }
.stage { flex: 1; display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(280px, .9fr); gap: 16px; }
.video-wrap {
  position: relative; border-radius: 20px; overflow: hidden;
  background: #060d16; border: 1px solid rgba(255, 255, 255, .08);
  min-height: 460px; display: flex; align-items: center; justify-content: center;
}
.video { width: 100%; height: 100%; object-fit: cover; display: block; }
.video.mirrored { transform: scaleX(-1); }
.video-placeholder {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 10px;
  color: #6f86a0; font-size: 13px; text-align: center; padding: 20px;
}
.video-placeholder .hint { font-size: 12px; color: #55697f; }
.scan-frame {
  position: absolute; width: 46%; aspect-ratio: 3 / 4;
  border: 2px dashed rgba(64, 158, 255, .55); border-radius: 18px;
  box-shadow: 0 0 50px rgba(64, 158, 255, .18) inset;
  pointer-events: none;
}
.badge {
  position: absolute; top: 14px; left: 14px;
  display: inline-flex; align-items: center; gap: 8px;
  padding: 7px 12px; border-radius: 999px; font-size: 12px;
  background: rgba(8, 18, 30, .72); border: 1px solid rgba(255, 255, 255, .12);
  color: #cfe0f2;
}
.overlay {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 10px;
  background: rgba(8, 20, 32, .88); text-align: center; padding: 24px;
}
.overlay.success { color: #3ddc84; }
.overlay.fail { color: #ff6b6b; }
.overlay-title { font-size: 26px; font-weight: 700; }
.overlay-sub { font-size: 13px; color: #a9bccf; }
.side { display: flex; flex-direction: column; gap: 14px; }
.stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.stat {
  background: rgba(255, 255, 255, .04); border: 1px solid rgba(255, 255, 255, .08);
  border-radius: 14px; padding: 12px 14px;
}
.stat .label { font-size: 11.5px; color: #7e96b1; }
.stat .value { font-size: 22px; font-weight: 700; margin-top: 4px; }
.stat .value.small { font-size: 16px; }
.stat .value.ok { color: #3ddc84; }
.panel-title { font-size: 12px; color: #7e96b1; letter-spacing: 1px; }
.records {
  flex: 1; background: rgba(255, 255, 255, .035); border: 1px solid rgba(255, 255, 255, .08);
  border-radius: 16px; padding: 10px; overflow-y: auto; min-height: 220px; max-height: 52vh;
}
.records .empty { color: #566b81; font-size: 12.5px; text-align: center; padding: 40px 0; }
.record { padding: 10px 12px; border-radius: 12px; margin-bottom: 8px; background: rgba(255, 255, 255, .04); border-left: 3px solid #3ddc84; }
.record.fail { border-left-color: #ff6b6b; }
.rec-main { display: flex; justify-content: space-between; font-size: 13.5px; }
.rec-main .name { font-weight: 600; }
.rec-main .sim { color: #8fb0cc; font-size: 12px; }
.rec-sub { font-size: 11.5px; color: #6f86a0; margin-top: 4px; }
.dup { color: #ffb454; margin-left: 6px; }
.tip { font-size: 11.5px; color: #5c738a; line-height: 1.7; }
.fade-enter-active, .fade-leave-active { transition: opacity .2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 900px) {
  .stage { grid-template-columns: 1fr; }
  .video-wrap { min-height: 58vh; }
  .side { flex-direction: column; }
  .records { max-height: 30vh; }
  .title { font-size: 17px; }
  .logo { width: 42px; height: 42px; font-size: 20px; }
  .controls { width: 100%; }
  .controls .el-select, .controls .el-button { flex: 1; }
}
</style>
