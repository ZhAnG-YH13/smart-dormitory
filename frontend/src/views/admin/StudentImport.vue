<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">批量导入学生</h2>
      <div>
        <el-button @click="$router.push('/students')">
          <el-icon><Back /></el-icon>返回学生列表
        </el-button>
      </div>
    </div>

    <div class="page-card">
      <div class="card-title">
        <span>模板列说明</span>
        <el-button type="primary" plain @click="downloadTemplate">
          <el-icon><Download /></el-icon>下载模板
        </el-button>
      </div>
      <el-table :data="sampleRows" border size="small">
        <el-table-column
          v-for="col in templateColumns"
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
          :width="col.width"
        />
      </el-table>
      <ul class="tip-list">
        <li>文件格式为 <b>.xlsx</b> 或 <b>.csv</b>，第一行为表头，必须与上表列名一致，从第二行开始填写学生数据。</li>
        <li>「学号」「姓名」为必填项；「性别」填写“男”或“女”。</li>
        <li>学院 / 专业 / 年级 / 班级 填写名称，系统会自动匹配，不存在的层级将自动创建。</li>
        <li>导入成功后系统会<b>自动为每名学生创建登录账号</b>（用户名=学号，初始密码 123456）。</li>
        <li>宿舍楼 / 宿舍房间 为选填信息，导入后可在学生编辑中补充。</li>
        <li>学号已存在的记录会被跳过并计入失败明细。</li>
      </ul>
    </div>

    <div class="page-card mt-16">
      <div class="card-title">
        <span>上传导入文件</span>
      </div>
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.csv"
        :on-change="onFileChange"
        :on-remove="onRemove"
        :on-exceed="onExceed"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将 Excel / CSV 文件拖到此处，或<em>点击选择文件</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 .xlsx / .csv 格式，单次只能上传一个文件</div>
        </template>
      </el-upload>

      <div class="import-actions">
        <el-button type="primary" :loading="importing" :disabled="!file" @click="doImport">
          <el-icon><Upload /></el-icon>开始导入
        </el-button>
        <el-button :disabled="importing" @click="resetUpload">清空</el-button>
        <span class="text-muted" v-if="file">已选择：{{ file.name }}</span>
      </div>
    </div>

    <template v-if="result">
      <div class="page-header mt-16">
        <h3 class="page-title result-title">导入结果</h3>
        <el-button v-if="errorRows.length" type="danger" plain @click="exportErrors">
          <el-icon><Download /></el-icon>导出失败记录
        </el-button>
      </div>

      <div class="stat-grid result-grid">
        <div class="stat-card" style="border-left-color: #409eff">
          <div class="label">总记录数</div>
          <div class="value">{{ totalCount }}<small>条</small></div>
        </div>
        <div class="stat-card" style="border-left-color: #67c23a">
          <div class="label">成功导入</div>
          <div class="value" style="color: #67c23a">{{ successCount }}<small>条</small></div>
        </div>
        <div class="stat-card" style="border-left-color: #f56c6c">
          <div class="label">导入失败</div>
          <div class="value" :style="{ color: failCount ? '#f56c6c' : '#1f2d3d' }">{{ failCount }}<small>条</small></div>
        </div>
      </div>

      <div class="page-card mt-16">
        <el-alert
          :type="failCount ? 'warning' : 'success'"
          :title="failCount ? `导入完成，其中 ${failCount} 条失败，请查看下方失败原因` : '全部学生导入成功'"
          show-icon
          :closable="false"
        />
        <div v-if="errorRows.length" class="error-table">
          <el-table :data="errorRows" border size="small" max-height="320">
            <el-table-column prop="index" label="序号" width="80" />
            <el-table-column prop="message" label="失败原因" min-width="400" />
          </el-table>
        </div>
        <div class="result-guide">
          <span class="text-muted">已导入学生，可前往学生列表批量创建账号。</span>
          <el-button type="primary" link @click="$router.push('/students')">前往学生列表</el-button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const uploadRef = ref(null)
const file = ref(null)
const importing = ref(false)
const result = ref(null)

const templateColumns = [
  { prop: 'student_no', label: '学号', width: 120 },
  { prop: 'name', label: '姓名', width: 90 },
  { prop: 'gender', label: '性别', width: 70 },
  { prop: 'college', label: '学院', width: 130 },
  { prop: 'major', label: '专业', width: 130 },
  { prop: 'grade', label: '年级', width: 90 },
  { prop: 'class_name', label: '班级', width: 110 },
  { prop: 'building', label: '宿舍楼', width: 100 },
  { prop: 'room', label: '宿舍房间', width: 100 },
  { prop: 'phone', label: '手机号', width: 130 }
]

const sampleRows = [
  {
    student_no: '20230001',
    name: '张三',
    gender: '男',
    college: '计算机学院',
    major: '软件工程',
    grade: '2023级',
    class_name: '软件2301',
    building: '1号楼',
    room: '301',
    phone: '13800000000'
  }
]

const successCount = computed(() => Number(result.value?.success_count) || 0)
const failCount = computed(() => Number(result.value?.fail_count) || 0)
const accountsCreated = computed(() => Number(result.value?.accounts_created) || 0)
const totalCount = computed(() => successCount.value + failCount.value)

const errorRows = computed(() => {
  const errors = result.value?.errors || []
  return errors.map((err, i) => {
    let message = ''
    if (typeof err === 'string') message = err
    else message = err?.message || JSON.stringify(err)
    return { index: i + 1, message }
  })
})

function onFileChange(uploadFile) {
  file.value = uploadFile.raw
}

function onRemove() {
  file.value = null
}

function onExceed() {
  ElMessage.warning('请先移除已选择的文件，再选择新的文件')
}

function resetUpload() {
  file.value = null
  result.value = null
  uploadRef.value?.clearFiles()
}

async function doImport() {
  if (!file.value) {
    ElMessage.warning('请先选择要导入的 Excel 文件')
    return
  }
  importing.value = true
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    result.value = await api.post('/students/import', formData)
    if (Number(result.value?.fail_count) > 0) {
      ElMessage.warning('导入完成，存在失败记录')
    } else {
      ElMessage.success(`导入完成：新增 ${successCount.value} 名学生，自动创建 ${accountsCreated.value} 个账号（初始密码 123456）`)
    }
  } catch (e) {
    /* 错误提示已由拦截器处理 */
  } finally {
    importing.value = false
  }
}

function downloadCsv(filename, rows) {
  const content = rows
    .map(row => row.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(','))
    .join('\r\n')
  const blob = new Blob(['\ufeff' + content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function downloadTemplate() {
  downloadCsv('学生导入模板.csv', [[
    '学号', '姓名', '性别', '学院', '专业', '年级', '班级', '宿舍楼', '宿舍房间', '手机号'
  ]])
  ElMessage.success('模板已开始下载')
}

function exportErrors() {
  if (!errorRows.value.length) return
  downloadCsv('失败记录.csv', [
    ['序号', '失败原因'],
    ...errorRows.value.map(r => [r.index, r.message])
  ])
}
</script>

<style scoped>
.card-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 15px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 14px;
}

.tip-list {
  margin: 14px 0 0;
  padding-left: 20px;
  color: #606266;
  font-size: 13px;
  line-height: 1.9;
}

.import-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 18px;
}

.result-title {
  margin: 0;
}

.result-grid {
  grid-template-columns: repeat(3, 1fr);
}

.error-table {
  margin-top: 14px;
}

.result-guide {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
}

@media (max-width: 768px) {
  .result-grid {
    grid-template-columns: 1fr;
  }
}
</style>
