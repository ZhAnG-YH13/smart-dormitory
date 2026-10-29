<template>
  <div v-loading="loading">
    <div class="page-card">
      <div class="page-header">
        <h2 class="page-title">我的信息</h2>
        <div>
          <el-button @click="loadData"><el-icon><Refresh /></el-icon>刷新</el-button>
          <el-button type="success" @click="$router.push('/student/face')">
            <el-icon><Avatar /></el-icon>去人脸注册
          </el-button>
        </div>
      </div>

      <el-empty v-if="!student" description="未找到学生档案" :image-size="90" />

      <template v-else>
        <div class="complete-head">
          <span class="complete-label">信息完整度</span>
          <span class="complete-value">{{ completion.info_complete ?? student.info_complete ?? 0 }}%</span>
          <span class="text-muted">
            已填写 {{ completion.filled_count ?? 0 }} / {{ completion.total_fields ?? 0 }} 项
          </span>
        </div>
        <el-progress
          :percentage="Number(completion.info_complete ?? student.info_complete ?? 0)"
          :stroke-width="14"
          :status="(completion.info_complete ?? student.info_complete) >= 100 ? 'success' : undefined"
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
      </template>
    </div>

    <div class="page-card mt-16">
      <h2 class="page-title">可编辑信息</h2>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" class="edit-form mt-16">
        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <el-form-item label="性别">
              <el-select v-model="form.gender" placeholder="请选择性别" style="width: 100%">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" placeholder="请输入手机号" clearable />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="身份证号" prop="id_card">
              <el-input v-model="form.id_card" placeholder="请输入身份证号" clearable />
            </el-form-item>
          </el-col>
        </el-row>
        <el-button type="primary" :loading="submitting" @click="submit">保存修改</el-button>
      </el-form>
    </div>

    <div class="page-card mt-16">
      <h2 class="page-title">学校维护信息（只读）</h2>
      <el-descriptions v-if="student" :column="2" border class="mt-16">
        <el-descriptions-item label="学号">{{ student.student_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ student.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="学院">{{ student.college_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="专业">{{ student.major_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="年级">{{ student.grade_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="班级">{{ student.class_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="宿舍" :span="2">
          {{ (student.building_name || '') + (student.room_number || '') || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const submitting = ref(false)
const student = ref(null)
const completion = ref({})
const formRef = ref(null)

const form = reactive({ gender: '', phone: '', id_card: '' })

const rules = {
  phone: [{ pattern: /^1\d{10}$/, message: '请输入正确的 11 位手机号', trigger: 'blur' }],
  id_card: [{ pattern: /^(\d{15}|\d{17}[\dXx])$/, message: '身份证号格式不正确', trigger: 'blur' }]
}

function genderValue(g) {
  if (g === 'M') return '男'
  if (g === 'F') return '女'
  return g || ''
}

async function loadData() {
  loading.value = true
  try {
    const res = await api.get('/students', { params: { page: 1, limit: 5 } })
    student.value = (res?.items || [])[0] || null
    if (!student.value) {
      completion.value = {}
      return
    }
    form.gender = genderValue(student.value.gender)
    form.phone = student.value.phone || ''
    form.id_card = student.value.id_card || ''

    const c = await api.get(`/students/${student.value.id}/info-complete`)
    completion.value = c || {}
  } catch (e) {
    // 错误提示已由拦截器处理
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!student.value) return
  const ok = await formRef.value.validate().catch(() => false)
  if (!ok) return
  submitting.value = true
  try {
    await api.put(`/students/${student.value.id}`, {
      gender: form.gender,
      phone: form.phone,
      id_card: form.id_card
    })
    ElMessage.success('个人信息保存成功')
    await loadData()
  } catch (e) {
    // 错误提示已由拦截器处理
  } finally {
    submitting.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.complete-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.complete-label {
  font-size: 14px;
  color: #606266;
}

.complete-value {
  font-size: 20px;
  font-weight: 600;
  color: #409eff;
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

.edit-form {
  max-width: 760px;
}
</style>
