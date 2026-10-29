<template>
  <div>
    <div class="page-header">
      <div>
        <h2 class="page-title">数据看板</h2>
        <div class="text-muted">智慧宿舍人脸门禁与学生管理系统 · 运行概览</div>
      </div>
      <el-button :loading="loading" @click="loadData">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>
    </div>

    <div class="stat-grid">
      <div v-for="item in cards" :key="item.label" class="stat-card" :style="{ borderLeftColor: item.color }">
        <div class="label">{{ item.label }}</div>
        <div class="value">{{ item.value }}<small>{{ item.unit }}</small></div>
      </div>
    </div>

    <el-row :gutter="14" class="mt-16">
      <el-col :xs="24" :md="12">
        <div class="page-card rate-card">
          <div class="card-title">
            <span>人脸注册率</span>
            <span class="text-muted">{{ stats.face_registered || 0 }} / {{ stats.total_students || 0 }} 人</span>
          </div>
          <el-progress :percentage="faceRate" :stroke-width="14" :color="faceColor" />
          <div class="text-muted mt-8">已完成人脸采集并注册的学生占比</div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="page-card rate-card">
          <div class="card-title">
            <span>摄像头在线率</span>
            <span class="text-muted">{{ stats.online_cameras || 0 }} / {{ stats.total_cameras || 0 }} 台</span>
          </div>
          <el-progress :percentage="onlineRate" :stroke-width="14" :color="onlineColor" />
          <div class="text-muted mt-8">在线设备占全部门禁摄像头的比例</div>
        </div>
      </el-col>
    </el-row>

    <div class="page-card mt-16">
      <div class="card-title">
        <span>最近 7 天通行趋势</span>
        <span class="text-muted">按日统计识别成功的通行次数</span>
      </div>
      <div ref="trendRef" class="chart-box"></div>
    </div>

    <el-row :gutter="14" class="mt-16">
      <el-col :xs="24" :md="8">
        <div class="page-card todo-card" @click="$router.push('/abnormals')">
          <div class="todo-head">
            <el-icon class="todo-icon" color="#f56c6c"><WarningFilled /></el-icon>
            <span class="card-title">待处理异常</span>
          </div>
          <div class="todo-value">{{ stats.pending_abnormal || 0 }}<small>条</small></div>
          <div class="todo-foot">
            <span class="text-muted">异常事件需尽快核实处理</span>
            <el-button link type="primary">前往异常中心</el-button>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :md="8">
        <div class="page-card todo-card" @click="$router.push('/faces')">
          <div class="todo-head">
            <el-icon class="todo-icon" color="#e6a23c"><Avatar /></el-icon>
            <span class="card-title">未注册人脸</span>
          </div>
          <div class="todo-value">{{ unregistered }}<small>人</small></div>
          <div class="todo-foot">
            <span class="text-muted">未注册将无法通过人脸门禁</span>
            <el-button link type="primary">前往人脸管理</el-button>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :md="8">
        <div class="page-card todo-card">
          <div class="todo-head">
            <el-icon class="todo-icon" color="#409eff"><VideoCamera /></el-icon>
            <span class="card-title">设备健康度</span>
          </div>
          <div v-if="devices" class="device-grid">
            <div><span class="text-muted">设备总数</span><b>{{ devices.total || 0 }}</b></div>
            <div><span class="text-muted">在线</span><b class="ok">{{ devices.online || 0 }}</b></div>
            <div><span class="text-muted">离线</span><b class="warn">{{ devices.offline || 0 }}</b></div>
            <div><span class="text-muted">故障</span><b class="danger">{{ devices.error || 0 }}</b></div>
          </div>
          <div v-else class="text-muted">暂无设备数据</div>
          <div class="todo-foot">
            <span class="text-muted">设备平均识别成功率 {{ deviceRecognitionRate }}%</span>
            <el-button link type="primary" @click="$router.push('/cameras')">查看设备</el-button>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'

const loading = ref(false)
const stats = ref({})
const devices = ref(null)
const trendRef = ref(null)
let chart = null

const cards = computed(() => [
  { label: '学生总数', value: stats.value.total_students || 0, unit: '人', color: '#409eff' },
  { label: '今日通行', value: stats.value.today_total || 0, unit: '次', color: '#67c23a' },
  { label: '今日进入（IN）', value: stats.value.today_in || 0, unit: '次', color: '#409eff' },
  { label: '今日离开（OUT）', value: stats.value.today_out || 0, unit: '次', color: '#909399' },
  { label: '当前在寝', value: stats.value.present_count || 0, unit: '人', color: '#e6a23c' },
  { label: '待处理异常', value: stats.value.pending_abnormal || 0, unit: '条', color: '#f56c6c' }
])

const faceRate = computed(() => Math.round((stats.value.face_register_rate || 0) * 100))
const onlineRate = computed(() => Math.round((stats.value.online_rate || 0) * 100))
const faceColor = computed(() => (faceRate.value >= 80 ? '#67c23a' : faceRate.value >= 50 ? '#e6a23c' : '#f56c6c'))
const onlineColor = computed(() => (onlineRate.value >= 90 ? '#67c23a' : onlineRate.value >= 60 ? '#e6a23c' : '#f56c6c'))
const unregistered = computed(() =>
  Math.max((stats.value.total_students || 0) - (stats.value.face_registered || 0), 0)
)
const deviceRecognitionRate = computed(() =>
  Math.round((devices.value?.avg_recognition_success_rate || 0) * 100)
)

async function loadData() {
  loading.value = true
  try {
    stats.value = await api.get('/stats/dashboard')
  } catch (e) {
    stats.value = {}
  } finally {
    loading.value = false
  }
  renderChart()
  try {
    devices.value = await api.get('/stats/devices')
  } catch (e) {
    devices.value = null
  }
}

function renderChart() {
  if (!trendRef.value) return
  const trend = stats.value.week_trend || []
  if (!chart) chart = echarts.init(trendRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 10, right: 20, top: 36, bottom: 10, containLabel: true },
    xAxis: {
      type: 'category',
      data: trend.map(t => t.date),
      axisLine: { lineStyle: { color: '#dcdfe6' } },
      axisLabel: { color: '#909399' }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: '#f0f2f5' } },
      axisLabel: { color: '#909399' }
    },
    series: [{
      name: '通行次数',
      type: 'bar',
      barWidth: '42%',
      data: trend.map(t => t.count),
      itemStyle: { color: '#409eff', borderRadius: [4, 4, 0, 0] },
      label: { show: true, position: 'top', color: '#606266' }
    }]
  })
}

function onResize() {
  chart && chart.resize()
}

onMounted(async () => {
  await loadData()
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.card-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 14px;
}

.rate-card {
  margin-bottom: 14px;
}

.mt-8 {
  margin-top: 10px;
}

.chart-box {
  width: 100%;
  height: 300px;
}

.todo-card {
  cursor: pointer;
  transition: box-shadow 0.2s;
  margin-bottom: 14px;
}

.todo-card:hover {
  box-shadow: 0 4px 14px rgba(64, 158, 255, 0.14);
}

.todo-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.todo-icon {
  font-size: 18px;
}

.todo-value {
  font-size: 30px;
  font-weight: 600;
  color: #1f2d3d;
  margin: 10px 0 6px;
}

.todo-value small {
  font-size: 13px;
  font-weight: 400;
  color: #909399;
  margin-left: 4px;
}

.todo-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.device-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 14px;
  margin: 8px 0 6px;
}

.device-grid div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f7f9fc;
  border-radius: 6px;
  padding: 6px 10px;
}

.device-grid b {
  font-size: 16px;
  color: #1f2d3d;
}

.device-grid b.ok {
  color: #67c23a;
}

.device-grid b.warn {
  color: #e6a23c;
}

.device-grid b.danger {
  color: #f56c6c;
}
</style>
