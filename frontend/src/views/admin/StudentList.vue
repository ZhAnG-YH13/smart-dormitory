<template>
  <div>
    <div class="page-header">
      <h2>学生列表</h2>
      <div>
        <el-button @click="loadData"><el-icon><Refresh /></el-icon>刷新</el-button>
        <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon>新增学生</el-button>
        <el-button type="success" @click="$router.push('/admin/students/import')"><el-icon><Upload /></el-icon>批量导入</el-button>
        <el-button type="warning" :disabled="!selectedIds.length" @click="batchCreateAccounts">
          <el-icon><User /></el-icon>批量创建账号
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-form :inline="true" :model="query" @submit.prevent>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="学号/姓名/手机号" clearable />
        </el-form-item>
        <el-form-item label="学院">
          <el-select v-model="query.college_id" placeholder="全部" clearable style="width:160px;">
            <el-option v-for="c in colleges" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="query.class_id" placeholder="全部" clearable style="width:160px;">
            <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="注册状态">
          <el-select v-model="query.face_status" placeholder="全部" clearable style="width:140px;">
            <el-option label="已注册" value="registered" />
            <el-option label="未注册" value="unregistered" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">搜索</el-button>
          <el-button @click="onReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-card">
      <el-table
        :data="list"
        v-loading="loading"
        stripe border
        @selection-change="selectedIds = $event.map(r => r.id)"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column label="学号" prop="student_no" width="140" />
        <el-table-column label="姓名" prop="name" width="100" />
        <el-table-column label="性别" prop="gender" width="70">
          <template #default="{ row }">{{ row.gender === 'M' ? '男' : row.gender === 'F' ? '女' : row.gender }}</template>
        </el-table-column>
        <el-table-column label="学院" prop="college_name" min-width="120" />
        <el-table-column label="专业" prop="major_name" min-width="120" />
        <el-table-column label="班级" prop="class_name" min-width="120" />
        <el-table-column label="宿舍" min-width="120">
          <template #default="{ row }">{{ row.building_name || '' }}{{ row.room_name || '' }}</template>
        </el-table-column>
        <el-table-column label="手机号" prop="phone" width="130" />
        <el-table-column label="人脸" width="90">
          <template #default="{ row }">
            <el-tag :type="row.face_registered ? 'success' : 'info'" size="small">
              {{ row.face_registered ? '已注册' : '未注册' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="warning" @click="onResetPwd(row)">重置密码</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:12px;display:flex;justify-content:flex-end;">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10,20,50,100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>

    <el-dialog v-model="show" :title="editing ? '编辑学生' : '新增学生'" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="学号" prop="student_no"><el-input v-model="form.student_no" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="姓名" prop="name"><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="性别"><el-select v-model="form.gender" style="width:100%;"><el-option label="男" value="M" /><el-option label="女" value="F" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="学院" prop="college_id"><el-select v-model="form.college_id" placeholder="请选择" style="width:100%;"><el-option v-for="c in colleges" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="专业" prop="major_id"><el-select v-model="form.major_id" placeholder="请选择" style="width:100%;"><el-option v-for="c in majors" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="年级" prop="grade_id"><el-select v-model="form.grade_id" placeholder="请选择" style="width:100%;"><el-option v-for="c in grades" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="班级" prop="class_id"><el-select v-model="form.class_id" placeholder="请选择" style="width:100%;"><el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="show = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getStudents, createStudent, updateStudent, deleteStudent, resetStudentPassword, createStudentAccounts } from '@/api/student'
import { getColleges, getMajors, getGrades, getClasses } from '@/api/organization'

const loading = ref(false)
const submitting = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const selectedIds = ref([])

const query = reactive({ keyword: '', college_id: '', class_id: '', face_status: '' })

const colleges = ref([])
const majors = ref([])
const grades = ref([])
const classes = ref([])

async function loadOptions() {
  try {
    const [c1, c2, c3, c4] = await Promise.all([
      getColleges(), getMajors(), getGrades(), getClasses()
    ])
    colleges.value = (c1.data || c1 || []).items || (c1.data || c1 || [])
    majors.value = (c2.data || c2 || []).items || (c2.data || c2 || [])
    grades.value = (c3.data || c3 || []).items || (c3.data || c3 || [])
    classes.value = (c4.data || c4 || []).items || (c4.data || c4 || [])
  } catch (e) { /* ignore */ }
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, limit: pageSize.value }
    if (query.keyword) params.keyword = query.keyword
    if (query.college_id) params.college_id = query.college_id
    if (query.class_id) params.class_id = query.class_id
    if (query.face_status) params.face_status = query.face_status
    const res = await getStudents(params)
    const data = res.data || res
    list.value = data.items || data.list || data.rows || data || []
    total.value = data.total || list.value.length
  } catch (e) { /* ignore */ }
  loading.value = false
}

function onSearch() { page.value = 1; loadData() }
function onReset() { Object.assign(query, { keyword: '', college_id: '', class_id: '', face_status: '' }); onSearch() }

const show = ref(false)
const editing = ref(null)
const formRef = ref(null)
const form = reactive({
  id: null, student_no: '', name: '', gender: 'M', phone: '',
  college_id: null, major_id: null, grade_id: null, class_id: null, remark: ''
})
const rules = {
  student_no: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }]
}

function openCreate() { editing.value = null; Object.assign(form, { id: null, student_no: '', name: '', gender: 'M', phone: '', college_id: null, major_id: null, grade_id: null, class_id: null, remark: '' }); show.value = true }
function openEdit(row) { editing.value = row.id; Object.assign(form, row); show.value = true }

async function submit() {
  const ok = await formRef.value.validate().catch(() => false)
  if (!ok) return
  submitting.value = true
  try {
    if (editing.value) await updateStudent(editing.value, form)
    else await createStudent(form)
    ElMessage.success(editing.value ? '更新成功' : '创建成功')
    show.value = false
    loadData()
  } catch (e) { /* ignore */ }
  submitting.value = false
}

function onDelete(row) {
  ElMessageBox.confirm(`确定删除学生 ${row.name} 吗？`, '提示', { type: 'warning' }).then(async () => {
    try {
      await deleteStudent(row.id); ElMessage.success('删除成功'); loadData()
    } catch (e) { /* ignore */ }
  }).catch(() => {})
}

function onResetPwd(row) {
  ElMessageBox.confirm(`确定重置 ${row.name} 的登录密码吗？`, '提示', { type: 'warning' }).then(async () => {
    try {
      const res = await resetStudentPassword(row.id)
      ElMessage.success(`密码已重置: ${res.data?.password || res.password || '123456'}`)
    } catch (e) { /* ignore */ }
  }).catch(() => {})
}

async function batchCreateAccounts() {
  if (!selectedIds.value.length) return
  try {
    await createStudentAccounts(selectedIds.value)
    ElMessage.success('批量创建账号成功')
  } catch (e) { /* ignore */ }
}

onMounted(() => { loadData(); loadOptions() })
</script>
