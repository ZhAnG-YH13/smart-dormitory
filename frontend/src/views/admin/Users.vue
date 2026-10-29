<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>新增用户
      </el-button>
    </div>

    <div class="page-card">
      <div class="toolbar">
        <el-select v-model="query.role" placeholder="全部角色" clearable style="width: 150px" @change="onSearch">
          <el-option label="管理员" value="admin" />
          <el-option label="辅导员" value="counselor" />
          <el-option label="学生" value="student" />
        </el-select>
        <el-input
          v-model="query.keyword"
          placeholder="用户名 / 姓名"
          clearable
          style="width: 220px"
          @keyup.enter="onSearch"
        />
        <el-button type="primary" @click="onSearch">搜索</el-button>
        <el-button @click="onReset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe border>
        <el-table-column label="用户名" prop="username" min-width="130" />
        <el-table-column label="姓名" prop="real_name" min-width="110" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small">{{ roleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="手机号" prop="phone" min-width="130" />
        <el-table-column label="邮箱" prop="email" min-width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="负责班级" min-width="130">
          <template #default="{ row }">
            {{ row.role === 'counselor' ? (row.counselor_class_name || '-') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="170">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="warning" @click="onResetPwd(row)">重置密码</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
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
          @size-change="load"
          @current-change="load"
        />
      </div>
    </div>

    <!-- 新增 / 编辑 -->
    <el-dialog v-model="show" :title="editingId ? '编辑用户' : '新增用户'" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" :disabled="!!editingId" placeholder="登录账号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="real_name">
              <el-input v-model="form.real_name" />
            </el-form-item>
          </el-col>
          <el-col v-if="!editingId" :span="12">
            <el-form-item label="初始密码">
              <el-input v-model="form.password" placeholder="留空则使用系统默认密码" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色" prop="role">
              <el-select v-model="form.role" style="width: 100%" @change="onRoleChange">
                <el-option label="管理员" value="admin" />
                <el-option label="辅导员" value="counselor" />
                <el-option label="学生" value="student" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="启用" :value="1" />
                <el-option label="禁用" :value="0" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机号">
              <el-input v-model="form.phone" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱">
              <el-input v-model="form.email" />
            </el-form-item>
          </el-col>
          <el-col v-if="form.role === 'counselor'" :span="24">
            <el-form-item label="负责班级">
              <el-select v-model="form.counselor_class_id" placeholder="请选择负责班级" clearable style="width: 100%">
                <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="show = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码结果 -->
    <el-dialog v-model="pwdVisible" title="密码已重置" width="420px">
      <div style="line-height: 1.8">
        <div>用户：<strong>{{ pwdInfo.name }}</strong></div>
        <div>新密码：<strong class="pwd-text">{{ pwdInfo.password }}</strong></div>
        <div class="text-muted mt-16">该用户下次登录后需修改密码，请及时告知本人。</div>
      </div>
      <template #footer>
        <el-button type="primary" @click="pwdVisible = false">知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const submitting = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const query = reactive({ role: '', keyword: '' })

const classes = ref([])

const show = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const form = reactive({
  username: '',
  real_name: '',
  password: '',
  phone: '',
  email: '',
  role: 'student',
  status: 1,
  counselor_class_id: null
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const pwdVisible = ref(false)
const pwdInfo = reactive({ name: '', password: '' })

function roleText(role) {
  const map = { admin: '管理员', counselor: '辅导员', student: '学生' }
  return map[role] || role || '-'
}

function roleTagType(role) {
  const map = { admin: 'danger', counselor: 'warning', student: 'success' }
  return map[role] || 'info'
}

function fmtTime(t) {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 19)
}

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, limit: pageSize.value }
    if (query.role) params.role = query.role
    if (query.keyword) params.keyword = query.keyword
    const res = await api.get('/users', { params })
    list.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
  loading.value = false
}

async function loadClasses() {
  try {
    const res = await api.get('/classes', { params: { limit: 100 } })
    classes.value = Array.isArray(res) ? res : (res.items || [])
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
}

function onSearch() {
  page.value = 1
  load()
}

function onReset() {
  query.role = ''
  query.keyword = ''
  onSearch()
}

function resetForm() {
  Object.assign(form, {
    username: '',
    real_name: '',
    password: '',
    phone: '',
    email: '',
    role: 'student',
    status: 1,
    counselor_class_id: null
  })
}

function openCreate() {
  editingId.value = null
  resetForm()
  show.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    username: row.username,
    real_name: row.real_name || '',
    password: '',
    phone: row.phone || '',
    email: row.email || '',
    role: row.role,
    status: row.status ?? 1,
    counselor_class_id: row.counselor_class_id ?? null
  })
  show.value = true
}

function onRoleChange() {
  if (form.role !== 'counselor') form.counselor_class_id = null
}

async function submit() {
  const ok = await formRef.value.validate().catch(() => false)
  if (!ok) return

  const payload = {
    real_name: form.real_name,
    phone: form.phone,
    email: form.email,
    role: form.role,
    status: form.status,
    counselor_class_id: form.role === 'counselor' ? form.counselor_class_id : null
  }

  submitting.value = true
  try {
    if (editingId.value) {
      await api.put(`/users/${editingId.value}`, payload)
      ElMessage.success('更新成功')
    } else {
      payload.username = form.username
      if (form.password) payload.password = form.password
      await api.post('/users', payload)
      ElMessage.success('创建成功')
    }
    show.value = false
    load()
  } catch (e) {
    /* 错误已由请求拦截器提示 */
  }
  submitting.value = false
}

function onResetPwd(row) {
  ElMessageBox.confirm(`确定重置用户「${row.real_name || row.username}」的登录密码吗？`, '重置密码', {
    type: 'warning',
    confirmButtonText: '确定重置',
    cancelButtonText: '取消'
  })
    .then(async () => {
      try {
        const res = await api.post(`/users/${row.id}/reset-password`, {})
        pwdInfo.name = row.real_name || row.username
        pwdInfo.password = res.new_password || res.default_password || res.password || '123456'
        pwdVisible.value = true
      } catch (e) {
        /* 错误已由请求拦截器提示 */
      }
    })
    .catch(() => {})
}

function onDelete(row) {
  ElMessageBox.confirm(`确定删除用户「${row.real_name || row.username}」吗？删除后不可恢复。`, '删除用户', {
    type: 'warning',
    confirmButtonText: '确定删除',
    cancelButtonText: '取消'
  })
    .then(async () => {
      try {
        await api.delete(`/users/${row.id}`)
        ElMessage.success('删除成功')
        load()
      } catch (e) {
        /* 错误已由请求拦截器提示 */
      }
    })
    .catch(() => {})
}

onMounted(() => {
  load()
  loadClasses()
})
</script>

<style scoped>
.pwd-text {
  color: #409eff;
  font-size: 16px;
  letter-spacing: 1px;
}
</style>
