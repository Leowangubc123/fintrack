<template>
  <div class="margin-import">
    <div class="annotation">
      每周导入四张Excel表格。个人余额表中，开发关系和服务关系在同一行并列展示。
    </div>

    <div class="import-grid">
      <div class="import-card">
        <div class="import-title">
          <div class="icon-circle">👤</div>
          个人余额
        </div>
        <div class="import-desc">
          包含字段：营业部、员工姓名、开发关系-两融余额(万)、服务关系-两融余额(万)<br>
          每位员工一行，开发和服务口径并列展示
        </div>
        <el-upload
          class="upload-area"
          drag
          :auto-upload="false"
          :on-change="handleFileChange($event, 'member_balance')"
          :limit="1"
          accept=".xlsx,.xls"
        >
          <el-icon class="upload-icon"><Upload /></el-icon>
          <div class="upload-text">拖拽文件到此处，或<em>点击上传</em></div>
        </el-upload>
        <el-button type="primary" style="margin-top: 16px; width: 100%;" :loading="importing.member_balance" @click="handleImport('member_balance')">
          开始导入
        </el-button>
      </div>

      <div class="import-card">
        <div class="import-title">
          <div class="icon-circle">🏢</div>
          营业部余额
        </div>
        <div class="import-desc">
          包含字段：营业部、时点余额(万)、日均余额(万)<br>
          每个营业部一行，展示时点余额和日均余额
        </div>
        <el-upload
          class="upload-area"
          drag
          :auto-upload="false"
          :on-change="handleFileChange($event, 'group_balance')"
          :limit="1"
          accept=".xlsx,.xls"
        >
          <el-icon class="upload-icon"><Upload /></el-icon>
          <div class="upload-text">拖拽文件到此处，或<em>点击上传</em></div>
        </el-upload>
        <el-button type="primary" style="margin-top: 16px; width: 100%;" :loading="importing.group_balance" @click="handleImport('group_balance')">
          开始导入
        </el-button>
      </div>

      <div class="import-card">
        <div class="import-title">
          <div class="icon-circle">💵</div>
          息费收入
        </div>
        <div class="import-desc">
          包含字段：营业部、本周息费收入(万)<br>
          按营业部统计本周两融息费收入数据
        </div>
        <el-upload
          class="upload-area"
          drag
          :auto-upload="false"
          :on-change="handleFileChange($event, 'income')"
          :limit="1"
          accept=".xlsx,.xls"
        >
          <el-icon class="upload-icon"><Upload /></el-icon>
          <div class="upload-text">拖拽文件到此处，或<em>点击上传</em></div>
        </el-upload>
        <el-button type="primary" style="margin-top: 16px; width: 100%;" :loading="importing.income" @click="handleImport('income')">
          开始导入
        </el-button>
      </div>

      <div class="import-card">
        <div class="import-title">
          <div class="icon-circle">📋</div>
          开户数据
        </div>
        <div class="import-desc">
          包含字段：开户日期、客户姓名、所属员工、营业部、开户资产(万)<br>
          每条开户记录一行
        </div>
        <el-upload
          class="upload-area"
          drag
          :auto-upload="false"
          :on-change="handleFileChange($event, 'new_account')"
          :limit="1"
          accept=".xlsx,.xls"
        >
          <el-icon class="upload-icon"><Upload /></el-icon>
          <div class="upload-text">拖拽文件到此处，或<em>点击上传</em></div>
        </el-upload>
        <el-button type="primary" style="margin-top: 16px; width: 100%;" :loading="importing.new_account" @click="handleImport('new_account')">
          开始导入
        </el-button>
      </div>
    </div>

    <!-- Import History -->
    <div class="history-card">
      <div class="history-title">导入历史</div>
      <el-table :data="importLogs" size="small" stripe>
        <el-table-column prop="data_type" label="数据类型" width="150">
          <template #default="{ row }">
            {{ getDataTypeLabel(row.data_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="import_date" label="导入日期" width="120" />
        <el-table-column prop="record_count" label="总条数" width="80" align="center" />
        <el-table-column prop="success_count" label="成功" width="80" align="center" />
        <el-table-column prop="error_count" label="失败" width="80" align="center" />
        <el-table-column prop="created_at" label="导入时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { marginTradingApi } from '../../api/marginTrading.js'

const importing = ref({
  member_balance: false,
  group_balance: false,
  income: false,
  new_account: false
})

const fileMap = ref({
  member_balance: null,
  group_balance: null,
  income: null,
  new_account: null
})

const importLogs = ref([])

const getCurrentWeek = () => {
  const now = new Date()
  const year = now.getFullYear()
  const oneJan = new Date(year, 0, 1)
  const weekNum = Math.ceil((((now - oneJan) / 86400000) + oneJan.getDay() + 1) / 7)
  return `${year}-W${String(weekNum).padStart(2, '0')}`
}

const handleFileChange = (file, dataType) => {
  fileMap.value[dataType] = file.raw
}

const handleImport = async (dataType) => {
  const file = fileMap.value[dataType]
  if (!file) {
    ElMessage.warning('请先上传文件')
    return
  }

  importing.value[dataType] = true
  try {
    const data = await readExcel(file)
    const recordWeek = getCurrentWeek()
    const recordDate = new Date().toISOString().split('T')[0]

    const res = await marginTradingApi.importData({
      data_type: dataType,
      record_week: recordWeek,
      record_date: recordDate,
      data: data
    })

    if (res.error_count === 0) {
      ElMessage.success(`导入成功：${res.success_count} 条`)
    } else {
      ElMessage.warning(`导入完成：${res.success_count} 条成功，${res.error_count} 条失败`)
      if (res.errors.length > 0) {
        console.warn('Import errors:', res.errors)
      }
    }

    fileMap.value[dataType] = null
    fetchImportLogs()
    window.dispatchEvent(new CustomEvent('margin-data-imported'))
  } catch (error) {
    console.error('Import error:', error)
    ElMessage.error('导入失败')
  } finally {
    importing.value[dataType] = false
  }
}

const readExcel = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result)
        const workbook = XLSX.read(data, { type: 'array' })
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
        const jsonData = XLSX.utils.sheet_to_json(firstSheet)
        resolve(jsonData)
      } catch (err) {
        reject(err)
      }
    }
    reader.onerror = reject
    reader.readAsArrayBuffer(file)
  })
}

const fetchImportLogs = async () => {
  try {
    const res = await marginTradingApi.getImportLogs(20)
    importLogs.value = res
  } catch (error) {
    console.error('Failed to fetch import logs:', error)
  }
}

const getDataTypeLabel = (type) => {
  const map = {
    'member_balance': '个人余额',
    'group_balance': '营业部余额',
    'income': '息费收入',
    'new_account': '开户数据'
  }
  return map[type] || type
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchImportLogs()
})
</script>

<style scoped>
.margin-import { padding: 0; }
.annotation {
  background: #F3E8FF; border-left: 3px solid #7C3AED;
  padding: 12px 16px; border-radius: 0 8px 8px 0;
  margin-bottom: 20px; font-size: 13px; color: #581C87;
}
.import-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;
  margin-bottom: 24px;
}
.import-card {
  background: white; border-radius: 12px; padding: 24px;
  border: 1px solid #E5E7EB; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.import-title {
  font-size: 15px; font-weight: 600; margin-bottom: 6px;
  display: flex; align-items: center; gap: 8px;
}
.icon-circle {
  width: 28px; height: 28px; border-radius: 8px;
  background: #F3E8FF; color: #7C3AED;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px;
}
.import-desc {
  color: #6B7280; font-size: 12px; margin-bottom: 16px; line-height: 1.5;
}
.upload-area {
  width: 100%;
}
.upload-area :deep(.el-upload-dragger) {
  border: 2px dashed #E5E7EB;
  border-radius: 10px;
  padding: 24px;
}
.upload-area :deep(.el-upload-dragger:hover) {
  border-color: #7C3AED;
  background: #FAFAFB;
}
.upload-icon {
  font-size: 28px; color: #7C3AED; margin-bottom: 8px;
}
.upload-text {
  font-size: 13px; color: #6B7280;
}
.upload-text em {
  color: #7C3AED; font-style: normal; font-weight: 500;
}
.history-card {
  background: white; border-radius: 12px; padding: 20px;
  border: 1px solid #E5E7EB; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.history-title {
  font-size: 15px; font-weight: 600; color: #111827;
  margin-bottom: 16px;
}
:deep(.el-button--primary) {
  background: #7C3AED; border-color: #7C3AED;
}
@media (max-width: 900px) {
  .import-grid { grid-template-columns: 1fr; }
}
</style>
