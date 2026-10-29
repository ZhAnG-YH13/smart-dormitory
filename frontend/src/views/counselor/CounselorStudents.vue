<template>
  <div class="page-card">
    <div class="page-header">
      <h2 class="page-title">我的班级 / 学生列表</h2>
      <el-button @click="loadData"><el-icon><Refresh /></el-icon>刷新</el-button>
    </div>

    <div class="toolbar">
      <el-input
        v-model="query.keyword"
        placeholder="学号 / 姓名 / 手机号"
        clearable
        style="width: 220px"
        @keyup.enter="onSearch"
      />
      <el-select v-model="query.face_status" placeholder="人脸状态" clearable style="width: 140px">
        <el-option label="已注册" value="registered" />
        <el-option label="未注册" value="unregistered" />
        <el-option label="注册中" value="registering" />
        <el-option label="注册失败" value="failed" />
        <el-option label="已注销" value="cancelled" />
      </el-select>
      <el-button type="primary" @click="onSearch">
        <el-icon><Search /></el-icon>查询
      </el-button>
      <el-button @click="onReset">重置</el-button>
    </div>

    <el-table v-loading="loading" :data="list" stripe border>
      <el-table-column label="学号" prop="student_no" width="130" />
      <el-table-column label="姓名" prop="name" width="90" />
      <el-table-column label="性别" width="70">
        <template #default="{ row }">{{ genderText(row.gender) }}</template>
      </el-table-column>
      <el-table-column label="班级" prop="class_name" min-width="130" show-overflow-tooltip />
      <el-table-column label="宿舍楼" prop="building_name" min-width="100" show-overflow-tooltip />
      <el-table-column label="房间" prop="room_number" width="90" />
      <el-table-column label="手机号" prop="phone" width="125" />
      <el-table-column label="信息完整度" width="150">
        <template #default="{ row }">
          <el-progress
            :percentage="Number(row.info_complete || 0)"
            :stroke-width="8"
            :status="row.info_complete >= 100 ? 'success' : undefined"
          />
        </template>
      </el-table-column>
      <el-table-column label="人脸状态" width="100">
        <template #default="{ row }">
          <el-tag :type="faceTag(row.face_status).type" size="small">
            {{ faceTag(row.face_status).text }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="loadData"
        @current-change="loadData"
      />
    </div>

    <el-dialog v-model="detailVisible" title="学生详情" width="760px">
      <div v-loading="detailLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="学号">{{ detail.student_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ detail.name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ genderText(detail.gender) }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ detail.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="身份证号">{{ detail.id_card || '-' }}</el-descriptions-item>
          <el-descriptions-item label="班级">{{ detail.class_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="学院">{{ detail.college_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="专业">{{ detail.major_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="年级">{{ detail.grade_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="宿舍">
            {{ (detail.building_name || '') + (detail.room_number || '') || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="人脸状态">
            <el-tag :type="faceTag(completion.face_status || detail.face_status).type" size="small">
              {{ faceTag(completion.face_status || detail.face_status).text }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="信息完整度">
            {{ completion.info_complete ?? detail.info_complete ?? 0 }}%
          </el-descriptions-item>
        </el-descriptions>

        <div class="section-title">字段填写情况</div>
        <el-progress
          :percentage="Number(completion.info_complete || 0)"
          :stroke-width="12"
          :status="completion.info_complete >= 100 ? 'success' : undefined"
        />
        <div class="field-grid mt-16">
          <div
            v-for="f in completion.fields || []"
            :key="f.key"
            class="field-item"
            :class="f.filled ? 'filled' : 'unfilled'"
          >
            <el-icon>
              <CircleCheck v-if="f.filled" />
              <CircleClose v-else />
            </el-icon>
            <span>{{ f.label }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/api'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

const query = reactive({ keyword: '', face_status: '' })

const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref({})
const completion = ref({})

const FACE_MAP = {
  registered: { text: '已注册', type: 'success' },
  unregistered: { text: '未注册', type: 'info' },
  registering: { text: '注册中', type: 'warning' },
  failed: { text: '注册失败', type: 'danger' },
  cancelled: { text: '已注销', type: 'info' }
}

function faceTag(status) {
  return FACE_MAP[status] || { text: status || '未注册', type: 'info' }
}

function genderText(g) {
  if (g === 'M' || g === '男') return '男'
  if (g === 'F' || g === '女') return '女'
  return g || '-'
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, limit: pageSize.value }
    if (query.keyword) params.keyword = query.keyword.trim()
    if (query.face_status) params.face_status = query.face_status
    const res = await api.get('/students', { params })
    list.value = res?.items || []
    total.value = res?.total || 0
  } catch (e) {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  loadData()
}

function onReset() {
  query.keyword = ''
  query.face_status = ''
  onSearch()
}

async function openDetail(row) {
  detailVisible.value = true
  detailLoading.value = true
  detail.value = row
  completion.value = {}
  try {
    const [d, c] = await Promise.all([
      api.get(`/students/${row.id}`),
      api.get(`/students/${row.id}/info-complete`)
    ])
    detail.value = d || row
    completion.value = c || {}
  } catch (e) {
    // 错误提示已由拦截器处理
  } finally {
    detailLoading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2d3d;
  margin: 18px 0 10px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 13px;
}

.field-item.filled {
  background: #f0f9eb;
  color: #67c23a;
}

.field-item.unfilled {
  background: #f4f4f5;
  color: #909399;
}
</style>
