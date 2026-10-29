<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">人脸注册情况</h2>
      <div>
        <el-button @click="loadAll"><el-icon><Refresh /></el-icon>刷新</el-button>
      </div>
    </div>

    <div class="stat-grid">
      <div class="stat-card">
        <div class="label">总人数</div>
        <div class="value">{{ stats.total ?? 0 }}<small>人</small></div>
      </div>
      <div class="stat-card" style="border-left-color: #67c23a">
        <div class="label">已注册人脸</div>
        <div class="value">{{ stats.face_registered ?? 0 }}<small>人</small></div>
      </div>
      <div class="stat-card" style="border-left-color: #e6a23c">
        <div class="label">人脸注册率</div>
        <div class="value">{{ percent(stats.face_register_rate) }}</div>
      </div>
      <div class="stat-card" style="border-left-color: #409eff">
        <div class="label">信息完整率</div>
        <div class="value">{{ percent(stats.info_complete_rate) }}</div>
      </div>
    </div>

    <el-alert
      class="mt-16"
      type="info"
      :closable="false"
      show-icon
      title="人脸注册由学生本人在「人脸注册」页完成，管理员仅查看注册情况，请勿代替学生上传人脸。"
    />

    <div class="page-card mt-16">
      <div class="toolbar">
        <el-input
          v-model="query.keyword"
          placeholder="学号 / 姓名 / 手机号"
          clearable
          style="width: 220px"
          @keyup.enter="onSearch"
        />
        <el-select v-model="query.face_status" placeholder="全部人脸状态" clearable style="width: 160px">
          <el-option label="未注册" value="unregistered" />
          <el-option label="已注册" value="registered" />
          <el-option label="注册失败" value="failed" />
        </el-select>
        <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon>搜索</el-button>
        <el-button @click="onReset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe border>
        <el-table-column label="学号" prop="student_no" width="140" />
        <el-table-column label="姓名" prop="name" width="100" />
        <el-table-column label="班级" prop="class_name" min-width="150">
          <template #default="{ row }">{{ row.class_name || '未分班' }}</template>
        </el-table-column>
        <el-table-column label="信息完整度" min-width="180">
          <template #default="{ row }">
            <el-progress
              :percentage="Number(row.info_complete) || 0"
              :stroke-width="9"
              :color="infoColor(row.info_complete)"
            />
          </template>
        </el-table-column>
        <el-table-column label="人脸状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="faceTagType(row.face_status)" size="small">{{ faceLabel(row.face_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openFaceStatus(row)">查看人脸状态</el-button>
            <el-button
              link
              type="danger"
              :disabled="row.face_status !== 'registered'"
              @click="onCancel(row)"
            >
              注销
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </div>

    <el-dialog v-model="faceVisible" title="人脸状态详情" width="600px">
      <div v-loading="faceLoading">
        <el-descriptions v-if="faceStatus" :column="2" border>
          <el-descriptions-item label="学生">{{ currentStudent?.name }} ({{ currentStudent?.student_no }})</el-descriptions-item>
          <el-descriptions-item label="人脸状态">
            <el-tag :type="faceTagType(faceStatus.face_status)" size="small">
              {{ faceLabel(faceStatus.face_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="是否已注册">
            <el-tag :type="faceStatus.registered ? 'success' : 'info'" size="small">
              {{ faceStatus.registered ? '是' : '否' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="人脸质量分">
            {{ faceStatus.quality_score != null ? Number(faceStatus.quality_score).toFixed(3) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="验证次数">{{ faceStatus.verify_count ?? 0 }}</el-descriptions-item>
          <el-descriptions-item label="验证成功次数">{{ faceStatus.verify_success_count ?? 0 }}</el-descriptions-item>
          <el-descriptions-item label="最近验证时间">{{ formatTime(faceStatus.last_verify_time) }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ formatTime(faceStatus.registered_at) }}</el-descriptions-item>
        </el-descriptions>
        <el-empty v-else description="暂无数据" :image-size="80" />
      </div>
      <template #footer>
        <el-button @click="faceVisible = false">关闭</el-button>
        <el-button type="primary" @click="loadFaceStatus">刷新</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const query = reactive({ keyword: '', face_status: '' })
const stats = ref({})

const faceVisible = ref(false)
const faceLoading = ref(false)
const faceStatus = ref(null)
const currentStudent = ref(null)

const faceMap = {
  registered: { label: '已注册', type: 'success' },
  unregistered: { label: '未注册', type: 'info' },
  registering: { label: '注册中', type: 'warning' },
  failed: { label: '注册失败', type: 'danger' },
  cancelled: { label: '已注销', type: 'info' }
}

function faceLabel(v) {
  return faceMap[v]?.label || v || '未注册'
}
function faceTagType(v) {
  return faceMap[v]?.type || 'info'
}
function percent(v) {
  if (v === null || v === undefined || v === '') return '-'
  return `${(Number(v) * 100).toFixed(1)}%`
}
function infoColor(v) {
  const n = Number(v) || 0
  if (n >= 80) return '#67c23a'
  if (n >= 50) return '#e6a23c'
  return '#f56c6c'
}
function formatTime(v) {
  if (!v) return '-'
  return String(v).replace('T', ' ').slice(0, 19)
}

async function loadStats() {
  try {
    stats.value = await api.get('/stats/students')
  } catch (e) {
    stats.value = {}
  }
}

async function loadList() {
  loading.value = true
  try {
    const params = { page: page.value, limit: pageSize.value }
    if (query.keyword) params.keyword = query.keyword
    if (query.face_status) params.face_status = query.face_status
    const res = await api.get('/students', { params })
    list.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  loadList()
}
function onReset() {
  Object.assign(query, { keyword: '', face_status: '' })
  onSearch()
}

async function loadFaceStatus() {
  if (!currentStudent.value) return
  faceLoading.value = true
  try {
    faceStatus.value = await api.get('/face/status', {
      params: { student_id: currentStudent.value.id }
    })
  } catch (e) {
    faceStatus.value = null
  } finally {
    faceLoading.value = false
  }
}

function openFaceStatus(row) {
  currentStudent.value = row
  faceStatus.value = null
  faceVisible.value = true
  loadFaceStatus()
}

function onCancel(row) {
  ElMessageBox.confirm(
    `确定注销「${row.name}」的人脸吗？注销后该学生将无法刷脸通行，需由学生本人重新注册，请谨慎操作。`,
    '人脸注销确认',
    { type: 'warning', confirmButtonText: '确定注销', cancelButtonText: '取消' }
  )
    .then(async () => {
      try {
        await api.delete('/face/cancel', { params: { student_id: row.id } })
        ElMessage.success('人脸已注销')
        loadList()
        loadStats()
        if (currentStudent.value?.id === row.id) loadFaceStatus()
      } catch (e) {
        /* 忽略 */
      }
    })
    .catch(() => {})
}

function loadAll() {
  loadStats()
  loadList()
}

onMounted(() => {
  loadStats()
  loadList()
})
</script>

<style scoped>
.stat-grid {
  margin-bottom: 0;
}
</style>
