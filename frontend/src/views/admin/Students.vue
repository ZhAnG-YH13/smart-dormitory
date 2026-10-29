<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">学生列表</h2>
      <div class="header-actions">
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>新增学生
        </el-button>
        <el-button :disabled="!selectedIds.length" @click="batchCreateAccounts">
          <el-icon><User /></el-icon>批量创建账号
        </el-button>
        <el-button @click="$router.push('/students/import')">
          <el-icon><Upload /></el-icon>批量导入
        </el-button>
      </div>
    </div>

    <div class="page-card">
      <div class="toolbar">
        <el-input
          v-model="query.keyword"
          placeholder="姓名 / 学号 / 手机号"
          clearable
          style="width: 230px"
          @keyup.enter="onSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="query.class_id" placeholder="全部班级" clearable filterable style="width: 190px">
          <el-option v-for="c in filterClasses" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-select v-model="query.face_status" placeholder="全部人脸状态" clearable style="width: 150px">
          <el-option label="已注册" value="registered" />
          <el-option label="未注册" value="unregistered" />
          <el-option label="注册失败" value="failed" />
        </el-select>
        <el-button type="primary" @click="onSearch">
          <el-icon><Search /></el-icon>查询
        </el-button>
        <el-button @click="onReset">
          <el-icon><Refresh /></el-icon>重置
        </el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="list"
        border
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="46" />
        <el-table-column prop="student_no" label="学号" width="130" />
        <el-table-column prop="name" label="姓名" width="90" />
        <el-table-column label="性别" width="70">
          <template #default="{ row }">{{ genderText(row.gender) }}</template>
        </el-table-column>
        <el-table-column prop="college_name" label="学院" min-width="130" show-overflow-tooltip />
        <el-table-column prop="major_name" label="专业" min-width="120" show-overflow-tooltip />
        <el-table-column prop="class_name" label="班级" min-width="120" show-overflow-tooltip />
        <el-table-column prop="building_name" label="宿舍楼" width="100" />
        <el-table-column prop="room_number" label="房间" width="80" />
        <el-table-column prop="phone" label="手机号" width="120" />
        <el-table-column label="信息完整度" width="130">
          <template #default="{ row }">
            <el-progress
              :percentage="Number(row.info_complete) || 0"
              :stroke-width="9"
              :color="completeColor(row.info_complete)"
            />
          </template>
        </el-table-column>
        <el-table-column label="人脸状态" width="105">
          <template #default="{ row }">
            <el-tag :type="faceTag(row.face_status).type" size="small">
              {{ faceTag(row.face_status).text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑学生' : '新增学生'" width="720px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="14">
          <el-col :span="12">
            <el-form-item label="学号" prop="student_no">
              <el-input v-model="form.student_no" placeholder="请输入学号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="form.name" placeholder="请输入姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别">
              <el-select v-model="form.gender" placeholder="请选择" style="width: 100%">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机号">
              <el-input v-model="form.phone" placeholder="请输入手机号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="身份证">
              <el-input v-model="form.id_card" placeholder="请输入身份证号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学院">
              <el-select
                v-model="form.college_id"
                placeholder="请选择学院"
                clearable
                filterable
                style="width: 100%"
                @change="onFormCollegeChange"
              >
                <el-option v-for="c in colleges" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="专业">
              <el-select
                v-model="form.major_id"
                placeholder="请选择专业"
                clearable
                filterable
                style="width: 100%"
                :disabled="!form.college_id"
                @change="onFormMajorChange"
              >
                <el-option v-for="m in formMajors" :key="m.id" :label="m.name" :value="m.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="年级">
              <el-select
                v-model="form.grade_id"
                placeholder="请选择年级"
                clearable
                filterable
                style="width: 100%"
                :disabled="!form.major_id"
                @change="onFormGradeChange"
              >
                <el-option v-for="g in formGrades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="班级">
              <el-select
                v-model="form.class_id"
                placeholder="请选择班级"
                clearable
                filterable
                style="width: 100%"
                :disabled="!form.grade_id"
              >
                <el-option v-for="c in formClasses" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="宿舍楼">
              <el-select
                v-model="form.building_id"
                placeholder="请选择宿舍楼"
                clearable
                filterable
                style="width: 100%"
                @change="onFormBuildingChange"
              >
                <el-option v-for="b in buildings" :key="b.id" :label="b.name" :value="b.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="宿舍房间">
              <el-select
                v-model="form.room_id"
                placeholder="请选择房间"
                clearable
                filterable
                style="width: 100%"
                :disabled="!form.building_id"
              >
                <el-option
                  v-for="r in formRooms"
                  :key="r.id"
                  :label="`${r.room_number}（${r.current_count || 0}/${r.capacity || 0}）`"
                  :value="r.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="学生详情" size="480px">
      <div v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="学号">{{ detail.student_no }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ detail.name }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ genderText(detail.gender) }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ detail.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="身份证" :span="2">{{ detail.id_card || '-' }}</el-descriptions-item>
          <el-descriptions-item label="学院">{{ detail.college_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="专业">{{ detail.major_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="年级">{{ detail.grade_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="班级">{{ detail.class_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="宿舍">{{ detail.building_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="房间">{{ detail.room_number || '-' }}</el-descriptions-item>
          <el-descriptions-item label="人脸状态">
            <el-tag :type="faceTag(detail.face_status).type" size="small">
              {{ faceTag(detail.face_status).text }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="信息完整度">
            {{ infoComplete.info_complete ?? detail.info_complete ?? 0 }}%
          </el-descriptions-item>
        </el-descriptions>

        <div class="detail-title">
          字段完整情况
          <span class="text-muted">
            {{ infoComplete.filled_count || 0 }} / {{ infoComplete.total_fields || 0 }}
          </span>
        </div>
        <div class="field-list">
          <div v-for="f in infoComplete.fields || []" :key="f.key" class="field-item">
            <el-icon :color="f.filled ? '#67c23a' : '#c0c4cc'" :size="16">
              <Check v-if="f.filled" />
              <Close v-else />
            </el-icon>
            <span :class="{ 'text-muted': !f.filled }">{{ f.label }}</span>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const FACE_MAP = {
  registered: { type: 'success', text: '已注册' },
  unregistered: { type: 'info', text: '未注册' },
  failed: { type: 'danger', text: '注册失败' },
  registering: { type: 'warning', text: '注册中' },
  cancelled: { type: 'info', text: '已注销' }
}

const loading = ref(false)
const submitting = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const selectedIds = ref([])
const query = reactive({ keyword: '', class_id: null, face_status: '' })

const filterClasses = ref([])
const colleges = ref([])
const buildings = ref([])
const formMajors = ref([])
const formGrades = ref([])
const formClasses = ref([])
const formRooms = ref([])

const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const form = reactive({
  student_no: '',
  name: '',
  gender: '男',
  phone: '',
  id_card: '',
  college_id: null,
  major_id: null,
  grade_id: null,
  class_id: null,
  building_id: null,
  room_id: null
})

const rules = {
  student_no: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }]
}

const detailVisible = ref(false)
const detail = ref(null)
const infoComplete = ref({})

function pickItems(res) {
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.items)) return res.items
  if (res?.data) return pickItems(res.data)
  return []
}

function genderText(gender) {
  if (gender === 'M') return '男'
  if (gender === 'F') return '女'
  return gender || '-'
}

function faceTag(status) {
  return FACE_MAP[status] || FACE_MAP.unregistered
}

function completeColor(value) {
  const n = Number(value) || 0
  if (n >= 80) return '#67c23a'
  if (n >= 50) return '#e6a23c'
  return '#f56c6c'
}

function handleSelectionChange(rows) {
  selectedIds.value = rows.map(r => r.id)
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, limit: pageSize.value }
    if (query.keyword) params.keyword = query.keyword
    if (query.class_id) params.class_id = query.class_id
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

async function loadOptions() {
  try {
    const [cls, cols, blds] = await Promise.all([
      api.get('/classes'),
      api.get('/colleges'),
      api.get('/buildings')
    ])
    filterClasses.value = pickItems(cls)
    colleges.value = pickItems(cols)
    buildings.value = pickItems(blds)
  } catch (e) {
    /* 选项加载失败已在拦截器提示 */
  }
}

function onSearch() {
  page.value = 1
  loadData()
}

function onReset() {
  query.keyword = ''
  query.class_id = null
  query.face_status = ''
  onSearch()
}

function resetForm() {
  Object.assign(form, {
    student_no: '',
    name: '',
    gender: '男',
    phone: '',
    id_card: '',
    college_id: null,
    major_id: null,
    grade_id: null,
    class_id: null,
    building_id: null,
    room_id: null
  })
  formMajors.value = []
  formGrades.value = []
  formClasses.value = []
  formRooms.value = []
}

function openCreate() {
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

async function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    student_no: row.student_no,
    name: row.name,
    gender: row.gender === 'M' ? '男' : row.gender === 'F' ? '女' : row.gender || '男',
    phone: row.phone || '',
    id_card: row.id_card || '',
    college_id: row.college_id || null,
    major_id: row.major_id || null,
    grade_id: row.grade_id || null,
    class_id: row.class_id || null,
    building_id: row.building_id || null,
    room_id: row.room_id || null
  })
  formMajors.value = []
  formGrades.value = []
  formClasses.value = []
  formRooms.value = []
  try {
    const [majors, grades, classes, rooms] = await Promise.all([
      row.college_id ? api.get('/majors', { params: { college_id: row.college_id } }) : Promise.resolve([]),
      row.major_id ? api.get('/grades', { params: { major_id: row.major_id } }) : Promise.resolve([]),
      row.grade_id ? api.get('/classes', { params: { grade_id: row.grade_id } }) : Promise.resolve([]),
      row.building_id ? api.get('/rooms', { params: { building_id: row.building_id, limit: 500 } }) : Promise.resolve([])
    ])
    formMajors.value = pickItems(majors)
    formGrades.value = pickItems(grades)
    formClasses.value = pickItems(classes)
    formRooms.value = pickItems(rooms)
  } catch (e) {
    /* ignore */
  }
  dialogVisible.value = true
}

async function onFormCollegeChange() {
  form.major_id = null
  form.grade_id = null
  form.class_id = null
  formMajors.value = []
  formGrades.value = []
  formClasses.value = []
  if (!form.college_id) return
  try {
    formMajors.value = pickItems(await api.get('/majors', { params: { college_id: form.college_id } }))
  } catch (e) {
    /* ignore */
  }
}

async function onFormMajorChange() {
  form.grade_id = null
  form.class_id = null
  formGrades.value = []
  formClasses.value = []
  if (!form.major_id) return
  try {
    formGrades.value = pickItems(await api.get('/grades', { params: { major_id: form.major_id } }))
  } catch (e) {
    /* ignore */
  }
}

async function onFormGradeChange() {
  form.class_id = null
  formClasses.value = []
  if (!form.grade_id) return
  try {
    formClasses.value = pickItems(await api.get('/classes', { params: { grade_id: form.grade_id } }))
  } catch (e) {
    /* ignore */
  }
}

async function onFormBuildingChange() {
  form.room_id = null
  formRooms.value = []
  if (!form.building_id) return
  try {
    formRooms.value = pickItems(await api.get('/rooms', { params: { building_id: form.building_id, limit: 500 } }))
  } catch (e) {
    /* ignore */
  }
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const payload = {
      student_no: form.student_no,
      name: form.name,
      gender: form.gender || null,
      phone: form.phone || null,
      id_card: form.id_card || null,
      college_id: form.college_id || null,
      major_id: form.major_id || null,
      grade_id: form.grade_id || null,
      class_id: form.class_id || null,
      building_id: form.building_id || null,
      room_id: form.room_id || null
    }
    if (editingId.value) {
      await api.put(`/students/${editingId.value}`, payload)
      ElMessage.success('学生信息已更新')
    } else {
      await api.post('/students', payload)
      ElMessage.success('学生创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    /* 错误提示已由拦截器处理 */
  } finally {
    submitting.value = false
  }
}

function onDelete(row) {
  ElMessageBox.confirm(`确定删除学生「${row.name}」（${row.student_no}）吗？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  })
    .then(async () => {
      try {
        await api.delete(`/students/${row.id}`)
        ElMessage.success('删除成功')
        loadData()
      } catch (e) {
        /* ignore */
      }
    })
    .catch(() => {})
}

async function openDetail(row) {
  detail.value = row
  infoComplete.value = {}
  detailVisible.value = true
  try {
    infoComplete.value = await api.get(`/students/${row.id}/info-complete`)
  } catch (e) {
    /* ignore */
  }
}

async function batchCreateAccounts() {
  if (!selectedIds.value.length) {
    ElMessage.warning('请先选择学生')
    return
  }
  try {
    const res = await api.post('/students/create-accounts', { student_ids: selectedIds.value })
    ElMessageBox.alert(
      `本次新建账号 ${res.created || 0} 个，跳过 ${res.skipped || 0} 个（已存在账号或学号冲突）。<br/>初始密码：<b>${res.default_password || '-'}</b>`,
      '批量创建账号结果',
      { dangerouslyUseHTMLString: true, confirmButtonText: '知道了' }
    ).catch(() => {})
  } catch (e) {
    /* ignore */
  }
}

onMounted(() => {
  loadData()
  loadOptions()
})
</script>

<style scoped>
.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.detail-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 600;
  color: #1f2d3d;
  margin: 20px 0 10px;
}

.field-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #f7f9fc;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 13px;
}
</style>
