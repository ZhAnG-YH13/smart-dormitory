<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">组织管理</h2>
      <el-button :loading="anyLoading" @click="reloadAll">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>
    </div>

    <div class="page-card">
      <el-tabs v-model="tab">
        <el-tab-pane label="学院" name="college">
          <div class="toolbar">
            <el-button type="primary" @click="openDialog('college')">
              <el-icon><Plus /></el-icon>新增学院
            </el-button>
            <span class="text-muted">共 {{ colleges.length }} 个学院</span>
          </div>
          <el-table v-loading="loading.college" :data="colleges" border stripe>
            <el-table-column prop="name" label="学院名称" min-width="200" />
            <el-table-column prop="code" label="学院编码" width="160">
              <template #default="{ row }">{{ row.code || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDialog('college', row)">编辑</el-button>
                <el-button link type="danger" @click="onDelete('college', row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="专业" name="major">
          <div class="toolbar">
            <el-select
              v-model="majorCollegeId"
              placeholder="全部学院"
              clearable
              filterable
              style="width: 210px"
              @change="loadMajors"
            >
              <el-option v-for="c in colleges" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-button type="primary" @click="openDialog('major')">
              <el-icon><Plus /></el-icon>新增专业
            </el-button>
            <span class="text-muted">共 {{ majors.length }} 个专业</span>
          </div>
          <el-table v-loading="loading.major" :data="majors" border stripe>
            <el-table-column prop="name" label="专业名称" min-width="200" />
            <el-table-column prop="college_name" label="所属学院" min-width="200" />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDialog('major', row)">编辑</el-button>
                <el-button link type="danger" @click="onDelete('major', row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="年级" name="grade">
          <div class="toolbar">
            <el-select
              v-model="gradeMajorId"
              placeholder="全部专业"
              clearable
              filterable
              style="width: 210px"
              @change="loadGrades"
            >
              <el-option v-for="m in majorsAll" :key="m.id" :label="m.name" :value="m.id" />
            </el-select>
            <el-button type="primary" @click="openDialog('grade')">
              <el-icon><Plus /></el-icon>新增年级
            </el-button>
            <span class="text-muted">共 {{ grades.length }} 个年级</span>
          </div>
          <el-table v-loading="loading.grade" :data="grades" border stripe>
            <el-table-column prop="name" label="年级名称" min-width="160" />
            <el-table-column prop="major_name" label="所属专业" min-width="160" />
            <el-table-column prop="college_name" label="所属学院" min-width="160" />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDialog('grade', row)">编辑</el-button>
                <el-button link type="danger" @click="onDelete('grade', row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="班级" name="class">
          <div class="toolbar">
            <el-select
              v-model="classGradeId"
              placeholder="全部年级"
              clearable
              filterable
              style="width: 210px"
              @change="loadClasses"
            >
              <el-option
                v-for="g in gradesAll"
                :key="g.id"
                :label="`${g.college_name || ''} ${g.major_name || ''} ${g.name}`"
                :value="g.id"
              />
            </el-select>
            <el-button type="primary" @click="openDialog('class')">
              <el-icon><Plus /></el-icon>新增班级
            </el-button>
            <span class="text-muted">共 {{ classes.length }} 个班级</span>
          </div>
          <el-table v-loading="loading.class" :data="classes" border stripe>
            <el-table-column prop="name" label="班级名称" min-width="140" />
            <el-table-column prop="grade_name" label="年级" min-width="110" />
            <el-table-column prop="major_name" label="专业" min-width="140" />
            <el-table-column prop="college_name" label="学院" min-width="140" />
            <el-table-column prop="counselor_name" label="辅导员" min-width="110">
              <template #default="{ row }">{{ row.counselor_name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="student_count" label="学生数" width="90" align="center" />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDialog('class', row)">编辑</el-button>
                <el-button link type="danger" @click="onDelete('class', row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" :placeholder="namePlaceholder" />
        </el-form-item>
        <el-form-item v-if="dialogType === 'college'" label="学院编码">
          <el-input v-model="form.code" placeholder="如 CS，选填" />
        </el-form-item>
        <el-form-item v-if="dialogType === 'major'" label="所属学院" prop="college_id">
          <el-select v-model="form.college_id" placeholder="请选择学院" filterable style="width: 100%">
            <el-option v-for="c in colleges" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="dialogType === 'grade'" label="所属专业" prop="major_id">
          <el-select v-model="form.major_id" placeholder="请选择专业" filterable style="width: 100%">
            <el-option
              v-for="m in majorsAll"
              :key="m.id"
              :label="`${m.college_name || ''} ${m.name}`"
              :value="m.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="dialogType === 'class'" label="所属年级" prop="grade_id">
          <el-select v-model="form.grade_id" placeholder="请选择年级" filterable style="width: 100%">
            <el-option
              v-for="g in gradesAll"
              :key="g.id"
              :label="`${g.major_name || ''} ${g.name}`"
              :value="g.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="dialogType === 'class'" label="辅导员">
          <el-select v-model="form.counselor_id" placeholder="请选择辅导员（选填）" clearable filterable style="width: 100%">
            <el-option
              v-for="u in counselors"
              :key="u.id"
              :label="`${u.real_name}（${u.username}）`"
              :value="u.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const urls = {
  college: '/colleges',
  major: '/majors',
  grade: '/grades',
  class: '/classes'
}
const typeLabels = {
  college: '学院',
  major: '专业',
  grade: '年级',
  class: '班级'
}
const placeholders = {
  college: '如 计算机学院',
  major: '如 软件工程',
  grade: '如 2023级',
  class: '如 软件2301'
}

const tab = ref('college')
const colleges = ref([])
const majors = ref([])
const majorsAll = ref([])
const grades = ref([])
const gradesAll = ref([])
const classes = ref([])
const counselors = ref([])

const majorCollegeId = ref(null)
const gradeMajorId = ref(null)
const classGradeId = ref(null)

const loading = reactive({ college: false, major: false, grade: false, class: false })
const anyLoading = computed(() => Object.values(loading).some(Boolean))

const dialogVisible = ref(false)
const dialogType = ref('college')
const editingId = ref(null)
const submitting = ref(false)
const formRef = ref(null)
const form = reactive({
  name: '',
  code: '',
  college_id: null,
  major_id: null,
  grade_id: null,
  counselor_id: null
})

const dialogTitle = computed(() => `${editingId.value ? '编辑' : '新增'}${typeLabels[dialogType.value]}`)
const namePlaceholder = computed(() => placeholders[dialogType.value])

const rules = computed(() => {
  const result = {
    name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
  }
  if (dialogType.value === 'major') {
    result.college_id = [{ required: true, message: '请选择所属学院', trigger: 'change' }]
  }
  if (dialogType.value === 'grade') {
    result.major_id = [{ required: true, message: '请选择所属专业', trigger: 'change' }]
  }
  if (dialogType.value === 'class') {
    result.grade_id = [{ required: true, message: '请选择所属年级', trigger: 'change' }]
  }
  return result
})

function pickItems(res) {
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.items)) return res.items
  if (res?.data) return pickItems(res.data)
  return []
}

async function loadColleges() {
  loading.college = true
  try {
    colleges.value = pickItems(await api.get('/colleges'))
  } catch (e) {
    colleges.value = []
  } finally {
    loading.college = false
  }
}

async function loadMajorsAll() {
  try {
    majorsAll.value = pickItems(await api.get('/majors'))
  } catch (e) {
    majorsAll.value = []
  }
}

async function loadGradesAll() {
  try {
    gradesAll.value = pickItems(await api.get('/grades'))
  } catch (e) {
    gradesAll.value = []
  }
}

async function loadMajors() {
  loading.major = true
  try {
    const params = majorCollegeId.value ? { college_id: majorCollegeId.value } : {}
    majors.value = pickItems(await api.get('/majors', { params }))
  } catch (e) {
    majors.value = []
  } finally {
    loading.major = false
  }
}

async function loadGrades() {
  loading.grade = true
  try {
    const params = gradeMajorId.value ? { major_id: gradeMajorId.value } : {}
    grades.value = pickItems(await api.get('/grades', { params }))
  } catch (e) {
    grades.value = []
  } finally {
    loading.grade = false
  }
}

async function loadClasses() {
  loading.class = true
  try {
    const params = classGradeId.value ? { grade_id: classGradeId.value } : {}
    classes.value = pickItems(await api.get('/classes', { params }))
  } catch (e) {
    classes.value = []
  } finally {
    loading.class = false
  }
}

async function loadCounselors() {
  try {
    counselors.value = pickItems(await api.get('/users', { params: { role: 'counselor', limit: 200 } }))
  } catch (e) {
    counselors.value = []
  }
}

async function reloadAll() {
  await Promise.all([
    loadColleges(),
    loadMajorsAll(),
    loadGradesAll(),
    loadMajors(),
    loadGrades(),
    loadClasses()
  ])
}

function openDialog(type, row = null) {
  dialogType.value = type
  editingId.value = row?.id || null
  form.name = row?.name || ''
  form.code = row?.code || ''
  form.college_id = row?.college_id ?? (type === 'major' ? majorCollegeId.value : null)
  form.major_id = row?.major_id ?? (type === 'grade' ? gradeMajorId.value : null)
  form.grade_id = row?.grade_id ?? (type === 'class' ? classGradeId.value : null)
  form.counselor_id = row?.counselor_id || null
  dialogVisible.value = true
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = { name: form.name }
    if (dialogType.value === 'college') payload.code = form.code || null
    if (dialogType.value === 'major') payload.college_id = form.college_id
    if (dialogType.value === 'grade') payload.major_id = form.major_id
    if (dialogType.value === 'class') {
      payload.grade_id = form.grade_id
      payload.counselor_id = form.counselor_id || null
    }

    const url = urls[dialogType.value]
    if (editingId.value) {
      await api.put(`${url}/${editingId.value}`, payload)
      ElMessage.success(`${typeLabels[dialogType.value]}已更新`)
    } else {
      await api.post(url, payload)
      ElMessage.success(`${typeLabels[dialogType.value]}已创建`)
    }
    dialogVisible.value = false
    await reloadAll()
  } catch (e) {
    /* 错误提示已由拦截器处理 */
  } finally {
    submitting.value = false
  }
}

function onDelete(type, row) {
  ElMessageBox.confirm(`确定删除${typeLabels[type]}「${row.name}」吗？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  })
    .then(async () => {
      try {
        await api.delete(`${urls[type]}/${row.id}`)
        ElMessage.success('删除成功')
        await reloadAll()
      } catch (e) {
        /* ignore */
      }
    })
    .catch(() => {})
}

onMounted(() => {
  loadColleges()
  loadMajorsAll()
  loadGradesAll()
  loadMajors()
  loadGrades()
  loadClasses()
  loadCounselors()
})
</script>

<style scoped>
.toolbar {
  margin-bottom: 14px;
}
</style>
