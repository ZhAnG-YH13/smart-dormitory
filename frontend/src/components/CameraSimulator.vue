<template>
  <div class="camera-simulator">
    <el-card shadow="never">
      <template #header>
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <span><el-icon><VideoCamera /></el-icon> 摄像头模拟器</span>
          <el-select v-model="selectedId" placeholder="选择摄像头" style="width:200px;" @change="onCameraChange">
            <el-option v-for="c in cameras" :key="c.id" :label="c.name" :value="c.id">
              <span>{{ c.name }}</span>
              <span style="float:right;color:#909399;font-size:12px;">{{ c.location || '' }}</span>
            </el-option>
          </el-select>
        </div>
      </template>

      <div v-if="currentCamera" style="margin-bottom:16px;">
        <div class="camera-panel" style="aspect-ratio:16/9;margin-bottom:12px;">
          <div class="camera-status">
            <span :class="currentCamera.status === 'online' ? 'status-online' : 'status-offline'">● {{ currentCamera.status === 'online' ? '在线' : '离线' }}</span>
          </div>
          <el-icon :size="48" color="#555"><VideoCamera /></el-icon>
          <div class="camera-name">{{ currentCamera.name }} — {{ currentCamera.location }}</div>
        </div>

        <div style="display:flex;gap:12px;justify-content:center;">
          <el-button type="primary" size="large" :loading="simulating" @click="doSimulate('IN')">
            <el-icon><CircleArrowDown /></el-icon> 模拟 进入
          </el-button>
          <el-button type="success" size="large" :loading="simulating" @click="doSimulate('OUT')">
            <el-icon><CircleArrowUp /></el-icon> 模拟 离开
          </el-button>
        </div>
      </div>
      <div v-else style="text-align:center;padding:40px;color:#909399;">
        请先选择一个摄像头
      </div>

      <el-divider>最近记录</el-divider>
      <div v-if="recentRecords.length">
        <div v-for="(r, i) in recentRecords.slice(0, 5)" :key="i"
             style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px dashed #ebeef5;font-size:13px;">
          <span>
            <el-tag :type="r.direction === 'IN' ? 'success' : 'warning'" size="small">{{ r.direction === 'IN' ? '进入' : '离开' }}</el-tag>
            <span style="margin-left:8px;">{{ r.student_name || r.name || '未知学生' }}</span>
          </span>
          <span style="color:#909399;">{{ r.time || r.created_at || '' }}</span>
        </div>
      </div>
      <div v-else style="text-align:center;color:#c0c4cc;padding:10px;">暂无记录</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getCameras, simulateCamera } from '@/api/camera'
import { getAccessRecords } from '@/api/access'
import { formatDateTime } from '@/utils/format'

const cameras = ref([])
const selectedId = ref(null)
const simulating = ref(false)
const recentRecords = ref([])

const currentCamera = ref(null)

async function loadCameras() {
  try {
    const res = await getCameras()
    const data = res.data || res
    cameras.value = Array.isArray(data) ? data : (data.items || data.list || data.rows || [])
    if (!selectedId.value && cameras.value.length) {
      selectedId.value = cameras.value[0].id
      onCameraChange()
    }
  } catch (e) { /* ignore */ }
}

function onCameraChange() {
  currentCamera.value = cameras.value.find(c => c.id === selectedId.value) || null
  loadRecords()
}

async function loadRecords() {
  try {
    const res = await getAccessRecords({ page: 1, limit: 10 })
    const data = res.data || res
    const list = Array.isArray(data) ? data : (data.items || data.list || [])
    recentRecords.value = list.map(r => ({
      ...r,
      time: formatDateTime(r.time || r.created_at)
    }))
  } catch (e) { /* ignore */ }
}

async function doSimulate(direction) {
  if (!selectedId.value) {
    ElMessage.warning('请先选择摄像头')
    return
  }
  simulating.value = true
  try {
    const res = await simulateCamera(selectedId.value, direction)
    ElMessage.success(`模拟${direction === 'IN' ? '进入' : '离开'}成功`)
    const record = res.data || res
    if (record && record !== true) {
      recentRecords.value.unshift({
        ...record,
        direction,
        time: formatDateTime(record.time || record.created_at || new Date())
      })
    }
  } catch (e) { /* ignore */ }
  simulating.value = false
}

onMounted(() => loadCameras())

defineExpose({ refresh: loadCameras })
</script>
