<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">数据统计</h2>
      <div class="toolbar" style="margin-bottom: 0">
        <span class="text-muted">门禁统计周期</span>
        <el-select v-model="days" style="width: 130px" @change="onDaysChange">
          <el-option label="最近 7 天" :value="7" />
          <el-option label="最近 14 天" :value="14" />
          <el-option label="最近 30 天" :value="30" />
        </el-select>
      </div>
    </div>

    <el-tabs v-model="activeTab">
      <!-- 学生统计 -->
      <el-tab-pane label="学生统计" name="students">
        <div v-loading="loading.students">
          <div class="stat-grid">
            <div class="stat-card">
              <div class="label">学生总数</div>
              <div class="value">{{ studentData?.total ?? 0 }}<small>人</small></div>
            </div>
            <div class="stat-card">
              <div class="label">已注册人脸</div>
              <div class="value">{{ studentData?.face_registered ?? 0 }}<small>人</small></div>
            </div>
            <div class="stat-card">
              <div class="label">人脸注册率</div>
              <div class="value">{{ pct(studentData?.face_register_rate) }}</div>
            </div>
            <div class="stat-card">
              <div class="label">信息完整率</div>
              <div class="value">{{ pct(studentData?.info_complete_rate) }}</div>
            </div>
          </div>

          <el-row :gutter="16" class="mt-16">
            <el-col :xs="24" :md="10">
              <div class="panel">
                <div class="panel-title">男女比例</div>
                <div ref="studentPieRef" class="chart"></div>
              </div>
            </el-col>
            <el-col :xs="24" :md="14">
              <div class="panel">
                <div class="panel-title">各学院人数</div>
                <div ref="studentBarRef" class="chart"></div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- 门禁统计 -->
      <el-tab-pane label="门禁统计" name="access">
        <div v-loading="loading.access">
          <div class="panel">
            <div class="panel-title">每日通行量（最近 {{ days }} 天）</div>
            <div ref="accessLineRef" class="chart"></div>
          </div>
          <div class="panel mt-16">
            <div class="panel-title">24 小时各时段流量</div>
            <div ref="accessBarRef" class="chart"></div>
          </div>
          <div class="panel mt-16">
            <div class="panel-title">各宿舍楼通行量（最近 {{ days }} 天）</div>
            <div ref="accessBuildingRef" class="chart"></div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 班级统计 -->
      <el-tab-pane label="班级统计" name="classes">
        <div v-loading="loading.classes">
          <div class="panel">
            <div class="panel-title">班级人脸注册率对比（共 {{ classData?.total_classes ?? 0 }} 个班级）</div>
            <div ref="classBarRef" class="chart"></div>
          </div>
          <div class="panel mt-16">
            <div class="panel-title">班级明细</div>
            <el-table :data="classData?.classes || []" stripe border max-height="420">
              <el-table-column label="班级" prop="class_name" min-width="160" />
              <el-table-column label="学生数" prop="total_students" width="90" />
              <el-table-column label="在寝" prop="present_count" width="80" />
              <el-table-column label="不在寝" prop="not_present_count" width="90" />
              <el-table-column label="已注册人脸" prop="face_registered" width="120" />
              <el-table-column label="待注册人脸" prop="unregistered_face" width="120" />
              <el-table-column label="人脸注册率" min-width="180">
                <template #default="{ row }">
                  <el-progress :percentage="ratePercent(row.face_register_rate)" :stroke-width="10" />
                </template>
              </el-table-column>
              <el-table-column label="信息完整率" min-width="180">
                <template #default="{ row }">
                  <el-progress
                    :percentage="ratePercent(row.info_complete_rate)"
                    :stroke-width="10"
                    color="#67c23a"
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <!-- 设备统计 -->
      <el-tab-pane label="设备统计" name="devices">
        <div v-loading="loading.devices">
          <div class="stat-grid">
            <div class="stat-card">
              <div class="label">设备总数</div>
              <div class="value">{{ deviceData?.total ?? 0 }}<small>台</small></div>
            </div>
            <div class="stat-card">
              <div class="label">在线设备</div>
              <div class="value">{{ deviceData?.online ?? 0 }}<small>台</small></div>
            </div>
            <div class="stat-card">
              <div class="label">设备在线率</div>
              <div class="value">{{ pct(deviceData?.online_rate) }}</div>
            </div>
            <div class="stat-card">
              <div class="label">平均识别成功率</div>
              <div class="value">{{ pct(deviceData?.avg_recognition_success_rate) }}</div>
            </div>
          </div>

          <el-row :gutter="16" class="mt-16">
            <el-col :xs="24" :md="10">
              <div class="panel">
                <div class="panel-title">设备状态分布</div>
                <div ref="devicePieRef" class="chart"></div>
              </div>
            </el-col>
            <el-col :xs="24" :md="14">
              <div class="panel">
                <div class="panel-title">各楼栋摄像头数量</div>
                <div ref="deviceBarRef" class="chart"></div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- 异常统计 -->
      <el-tab-pane label="异常统计" name="abnormals">
        <div v-loading="loading.abnormals">
          <div class="stat-grid">
            <div class="stat-card">
              <div class="label">异常总数</div>
              <div class="value">{{ abnormalData?.total ?? 0 }}<small>条</small></div>
            </div>
            <div class="stat-card">
              <div class="label">待处理</div>
              <div class="value">{{ abnormalData?.pending ?? 0 }}<small>条</small></div>
            </div>
            <div class="stat-card">
              <div class="label">处理中</div>
              <div class="value">{{ abnormalData?.processing ?? 0 }}<small>条</small></div>
            </div>
            <div class="stat-card">
              <div class="label">解决率</div>
              <div class="value">{{ pct(abnormalData?.resolve_rate) }}</div>
            </div>
          </div>

          <el-row :gutter="16" class="mt-16">
            <el-col :xs="24" :md="12">
              <div class="panel">
                <div class="panel-title">按异常类型分布</div>
                <div ref="abnormalPieRef" class="chart"></div>
              </div>
            </el-col>
            <el-col :xs="24" :md="12">
              <div class="panel">
                <div class="panel-title">按严重程度分布</div>
                <div ref="abnormalBarRef" class="chart"></div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- AI 识别统计 -->
      <el-tab-pane label="AI 识别统计" name="ai">
        <div v-loading="loading.ai">
          <div class="stat-grid">
            <div class="stat-card">
              <div class="label">检测次数</div>
              <div class="value">{{ aiData?.total_detections ?? 0 }}<small>次</small></div>
            </div>
            <div class="stat-card">
              <div class="label">识别成功</div>
              <div class="value">{{ aiData?.success_count ?? 0 }}<small>次</small></div>
            </div>
            <div class="stat-card">
              <div class="label">识别失败</div>
              <div class="value">{{ aiData?.fail_count ?? 0 }}<small>次</small></div>
            </div>
            <div class="stat-card">
              <div class="label">未检测到人脸</div>
              <div class="value">{{ aiData?.no_face_count ?? 0 }}<small>次</small></div>
            </div>
            <div class="stat-card">
              <div class="label">平均识别耗时</div>
              <div class="value">{{ aiData?.avg_recognition_ms ?? 0 }}<small>ms</small></div>
            </div>
            <div class="stat-card">
              <div class="label">识别成功率</div>
              <div class="value">{{ pct(aiData?.success_rate) }}</div>
            </div>
          </div>

          <el-row :gutter="16" class="mt-16">
            <el-col :xs="24" :md="16">
              <div class="panel">
                <div class="panel-title">每日识别趋势（最近 {{ days }} 天）</div>
                <div ref="aiLineRef" class="chart"></div>
              </div>
            </el-col>
            <el-col :xs="24" :md="8">
              <div class="panel">
                <div class="panel-title">识别失败原因</div>
                <div ref="aiFailRef" class="chart"></div>
              </div>
            </el-col>
          </el-row>

          <div class="panel mt-16">
            <div class="panel-title">AI 引擎信息</div>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="识别后端">{{ aiData?.engine?.backend || '-' }}</el-descriptions-item>
              <el-descriptions-item label="识别模型">{{ aiData?.engine?.model || '-' }}</el-descriptions-item>
              <el-descriptions-item label="OpenCV 版本">{{ aiData?.engine?.opencv_version || '-' }}</el-descriptions-item>
              <el-descriptions-item label="NumPy 版本">{{ aiData?.engine?.numpy_version || '-' }}</el-descriptions-item>
              <el-descriptions-item label="相似度阈值">{{ aiData?.similarity_threshold ?? '-' }}</el-descriptions-item>
              <el-descriptions-item label="成功平均相似度">{{ aiData?.avg_success_similarity ?? '-' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, watch, nextTick, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'

const activeTab = ref('students')
const days = ref(7)

const loading = reactive({ students: false, access: false, classes: false, devices: false, abnormals: false, ai: false })
const loaded = reactive({ students: false, access: false, classes: false, devices: false, abnormals: false, ai: false })

const studentData = ref(null)
const accessData = ref(null)
const classData = ref(null)
const deviceData = ref(null)
const abnormalData = ref(null)
const aiData = ref(null)

const studentPieRef = ref(null)
const studentBarRef = ref(null)
const accessLineRef = ref(null)
const accessBarRef = ref(null)
const accessBuildingRef = ref(null)
const classBarRef = ref(null)
const devicePieRef = ref(null)
const deviceBarRef = ref(null)
const abnormalPieRef = ref(null)
const abnormalBarRef = ref(null)
const aiLineRef = ref(null)
const aiFailRef = ref(null)

const charts = {}

const typeTextMap = {
  tailgating: '尾随进入',
  loitering: '区域逗留',
  face_mismatch: '人脸不匹配',
  card_invalid: '证件无效',
  device_offline: '设备离线',
  density_high: '密度过高',
  night_out: '夜间未归',
  late_return: '晚归'
}
const severityTextMap = { low: '低', medium: '中', high: '高', critical: '紧急' }

function pct(v) {
  return `${((Number(v) || 0) * 100).toFixed(1)}%`
}

function ratePercent(v) {
  return Number(((Number(v) || 0) * 100).toFixed(1))
}

function renderChart(key, el, option) {
  if (!el.value) return
  if (charts[key]) {
    charts[key].dispose()
    delete charts[key]
  }
  const instance = echarts.init(el.value)
  instance.setOption(option)
  charts[key] = instance
}

async function loadStudents() {
  loading.students = true
  try {
    studentData.value = await api.get('/stats/students')
    loaded.students = true
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
  loading.students = false
}

async function loadAccess() {
  loading.access = true
  try {
    accessData.value = await api.get('/stats/access', { params: { days: days.value } })
    loaded.access = true
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
  loading.access = false
}

async function loadClasses() {
  loading.classes = true
  try {
    classData.value = await api.get('/stats/classes')
    loaded.classes = true
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
  loading.classes = false
}

async function loadDevices() {
  loading.devices = true
  try {
    deviceData.value = await api.get('/stats/devices')
    loaded.devices = true
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
  loading.devices = false
}

async function loadAbnormals() {
  loading.abnormals = true
  try {
    abnormalData.value = await api.get('/stats/abnormals')
    loaded.abnormals = true
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
  loading.abnormals = false
}

async function loadAi() {
  loading.ai = true
  try {
    aiData.value = await api.get('/stats/ai', { params: { days: days.value } })
    loaded.ai = true
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
  loading.ai = false
}

function renderStudents() {
  const d = studentData.value || {}
  renderChart('studentPie', studentPieRef, {
    tooltip: { trigger: 'item', formatter: '{b}: {c} 人 ({d}%)' },
    legend: { bottom: 0, icon: 'circle' },
    color: ['#409eff', '#f56c6c'],
    series: [
      {
        name: '男女比例',
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['50%', '45%'],
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { formatter: '{b}\n{c} 人' },
        data: [
          { value: d.male_count || 0, name: '男生' },
          { value: d.female_count || 0, name: '女生' }
        ]
      }
    ]
  })

  const colleges = d.colleges || []
  renderChart('studentBar', studentBarRef, {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: colleges.map(c => c.college_name),
      axisLabel: { interval: 0, rotate: colleges.length > 6 ? 30 : 0 }
    },
    yAxis: { type: 'value', name: '人数' },
    series: [
      {
        name: '学生人数',
        type: 'bar',
        barMaxWidth: 40,
        data: colleges.map(c => c.count || 0),
        itemStyle: { color: '#1e3c72', borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: 'top' }
      }
    ]
  })
}

function renderAccess() {
  const d = accessData.value || {}
  const daily = d.daily || []
  renderChart('accessLine', accessLineRef, {
    tooltip: { trigger: 'axis' },
    legend: { data: ['总通行量', '成功', '失败'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '6%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: daily.map(x => String(x.date || '').slice(5)) },
    yAxis: { type: 'value', name: '次数' },
    series: [
      { name: '总通行量', type: 'line', smooth: true, data: daily.map(x => x.total || 0), itemStyle: { color: '#1e3c72' } },
      { name: '成功', type: 'line', smooth: true, data: daily.map(x => x.success || 0), itemStyle: { color: '#67c23a' } },
      { name: '失败', type: 'line', smooth: true, data: daily.map(x => x.failed || 0), itemStyle: { color: '#f56c6c' } }
    ]
  })

  const hourly = d.hourly || []
  renderChart('accessBar', accessBarRef, {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '6%', containLabel: true },
    xAxis: { type: 'category', data: hourly.map(h => `${h.hour}时`), axisLabel: { interval: 1 } },
    yAxis: { type: 'value', name: '次数' },
    series: [
      {
        name: '通行量',
        type: 'bar',
        barMaxWidth: 18,
        data: hourly.map(h => h.count || 0),
        itemStyle: { color: '#409eff', borderRadius: [4, 4, 0, 0] }
      }
    ]
  })

  const buildings = d.by_building || []
  renderChart('accessBuilding', accessBuildingRef, {
    tooltip: { trigger: 'axis' },
    legend: { data: ['成功', '失败'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '8%', containLabel: true },
    xAxis: { type: 'category', data: buildings.map(b => b.building_name), axisLabel: { interval: 0 } },
    yAxis: { type: 'value', name: '次数' },
    series: [
      {
        name: '成功',
        type: 'bar',
        stack: 'total',
        barMaxWidth: 32,
        data: buildings.map(b => b.success || 0),
        itemStyle: { color: '#67c23a' }
      },
      {
        name: '失败',
        type: 'bar',
        stack: 'total',
        barMaxWidth: 32,
        data: buildings.map(b => b.failed || 0),
        itemStyle: { color: '#f56c6c', borderRadius: [4, 4, 0, 0] }
      }
    ]
  })
}

function renderClasses() {
  const rows = (classData.value?.classes) || []
  renderChart('classBar', classBarRef, {
    tooltip: { trigger: 'axis', valueFormatter: v => `${v}%` },
    grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', max: 100, name: '注册率(%)' },
    yAxis: { type: 'category', data: rows.map(r => r.class_name) },
    series: [
      {
        name: '人脸注册率',
        type: 'bar',
        barMaxWidth: 18,
        data: rows.map(r => ratePercent(r.face_register_rate)),
        itemStyle: { color: '#67c23a', borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: 'right', formatter: '{c}%' }
      }
    ]
  })
}

function renderDevices() {
  const d = deviceData.value || {}
  renderChart('devicePie', devicePieRef, {
    tooltip: { trigger: 'item', formatter: '{b}: {c} 台 ({d}%)' },
    legend: { bottom: 0, icon: 'circle' },
    color: ['#67c23a', '#909399', '#f56c6c', '#e6a23c'],
    series: [
      {
        name: '设备状态',
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['50%', '45%'],
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { formatter: '{b}\n{c} 台' },
        data: [
          { value: d.online || 0, name: '在线' },
          { value: d.offline || 0, name: '离线' },
          { value: d.error || 0, name: '异常' },
          { value: d.maintenance || 0, name: '维护中' }
        ]
      }
    ]
  })

  const buildings = d.buildings || []
  renderChart('deviceBar', deviceBarRef, {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '8%', containLabel: true },
    xAxis: { type: 'category', data: buildings.map(b => b.name), axisLabel: { interval: 0, rotate: buildings.length > 6 ? 30 : 0 } },
    yAxis: { type: 'value', name: '摄像头数' },
    series: [
      {
        name: '摄像头数量',
        type: 'bar',
        barMaxWidth: 40,
        data: buildings.map(b => b.camera_count || 0),
        itemStyle: { color: '#409eff', borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: 'top' }
      }
    ]
  })
}

function renderAbnormals() {
  const d = abnormalData.value || {}
  renderChart('abnormalPie', abnormalPieRef, {
    tooltip: { trigger: 'item', formatter: '{b}: {c} 条 ({d}%)' },
    legend: { bottom: 0, icon: 'circle' },
    series: [
      {
        name: '异常类型',
        type: 'pie',
        radius: ['40%', '64%'],
        center: ['50%', '45%'],
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { formatter: '{b}\n{c} 条' },
        data: (d.by_type || []).map(t => ({
          value: t.count || 0,
          name: typeTextMap[t.type] || t.type || '未知'
        }))
      }
    ]
  })

  const severities = d.by_severity || []
  renderChart('abnormalBar', abnormalBarRef, {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '8%', containLabel: true },
    xAxis: { type: 'category', data: severities.map(s => severityTextMap[s.severity] || s.severity || '未知'), axisLabel: { interval: 0 } },
    yAxis: { type: 'value', name: '数量' },
    series: [
      {
        name: '异常数量',
        type: 'bar',
        barMaxWidth: 40,
        data: severities.map(s => s.count || 0),
        itemStyle: { color: '#e6a23c', borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: 'top' }
      }
    ]
  })
}

const reasonTextMap = {
  FACE_MISMATCH: '人脸不匹配',
  NO_MATCH_FOUND: '未匹配到已注册人脸',
  NO_FACE_DETECTED: '未检测到人脸',
  FACE_NOT_FOUND: '未检测到人脸',
  FACE_TOO_BLUR: '人脸模糊',
  FACE_TOO_DARK: '光线过暗',
  FACE_TOO_BRIGHT: '光线过亮',
  FACE_TOO_SMALL: '人脸过小'
}

function renderAi() {
  const d = aiData.value || {}
  const daily = d.daily || []
  renderChart('aiLine', aiLineRef, {
    tooltip: { trigger: 'axis' },
    legend: { data: ['检测次数', '成功', '失败'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '6%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: daily.map(x => x.date) },
    yAxis: { type: 'value', name: '次数' },
    series: [
      { name: '检测次数', type: 'line', smooth: true, data: daily.map(x => x.detections || 0), itemStyle: { color: '#1e3c72' } },
      { name: '成功', type: 'line', smooth: true, data: daily.map(x => x.success || 0), itemStyle: { color: '#67c23a' } },
      { name: '失败', type: 'line', smooth: true, data: daily.map(x => x.failed || 0), itemStyle: { color: '#f56c6c' } }
    ]
  })

  const reasons = d.fail_reasons || []
  renderChart('aiFail', aiFailRef, {
    tooltip: { trigger: 'item', formatter: '{b}: {c} 次 ({d}%)' },
    legend: { bottom: 0, icon: 'circle' },
    series: [
      {
        name: '失败原因',
        type: 'pie',
        radius: ['40%', '64%'],
        center: ['50%', '45%'],
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { formatter: '{b}\n{c} 次' },
        data: reasons.length
          ? reasons.map(r => ({ value: r.count || 0, name: reasonTextMap[r.reason] || r.reason }))
          : [{ value: 1, name: '暂无失败记录', itemStyle: { color: '#dcdfe6' } }]
      }
    ]
  })
}

const loaders = {
  students: loadStudents,
  access: loadAccess,
  classes: loadClasses,
  devices: loadDevices,
  abnormals: loadAbnormals,
  ai: loadAi
}

const renderers = {
  students: renderStudents,
  access: renderAccess,
  classes: renderClasses,
  devices: renderDevices,
  abnormals: renderAbnormals,
  ai: renderAi
}

async function activateTab(tab) {
  if (!loaded[tab]) await loaders[tab]()
  await nextTick()
  renderers[tab]()
}

function onDaysChange() {
  loaded.access = false
  loaded.ai = false
  if (activeTab.value === 'access') activateTab('access')
  if (activeTab.value === 'ai') activateTab('ai')
}

function resizeCharts() {
  Object.keys(charts).forEach(key => charts[key].resize())
}

watch(activeTab, tab => activateTab(tab))

onMounted(() => {
  activateTab('students')
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  Object.keys(charts).forEach(key => {
    charts[key].dispose()
    delete charts[key]
  })
})
</script>

<style scoped>
.panel {
  background: #fff;
  border-radius: 10px;
  padding: 16px 18px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 12px;
}

.chart {
  width: 100%;
  height: 320px;
}
</style>
