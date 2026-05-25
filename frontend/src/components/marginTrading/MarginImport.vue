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
          :on-change="(file) => handleFileChange(file, 'member_balance')"
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
          支持双Sheet：营业部时点余额 + 营业部日均余额<br>
          自动抓取：机构名称 → 时点/日均融资融券余额（元→万元）<br>
          自动映射营业部名称，合并同一营业部时点和日均数据
        </div>
        <el-upload
          class="upload-area"
          drag
          :auto-upload="false"
          :on-change="(file) => handleFileChange(file, 'group_balance')"
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
          :on-change="(file) => handleFileChange(file, 'income')"
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
          :on-change="(file) => handleFileChange(file, 'new_account')"
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
import { marginTradingApi } from '../../api/marginTrading.js'

// 动态导入 xlsx，避免构建时阻塞
let XLSX = null
const loadXlsx = async () => {
  if (!XLSX) {
    XLSX = await import('xlsx')
  }
  return XLSX
}

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
    const data = await readExcel(file, dataType)
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

// 营业部名称映射：Excel中的名称 -> 系统中的名称
const groupNameMapping = {
  '上海延安西路营业部': '上一',
  '上海民生路营业部': '上二',
  '上海分公司': '上海分公司',
  '上海黄浦区西藏中路营业部': '上五',
  '上海向城路营业部': '上六',
  '上海金吉路营业部': '上三',
  '上海静安区北苏州路营业部': '上四'
}

// 将Excel列名中的空格去除
const normalizeColName = (name) => {
  if (!name) return ''
  return String(name).replace(/\s+/g, '').trim()
}

// 自动识别sheet中的列索引
const detectColumns = (headers) => {
  const normalized = headers.map(h => normalizeColName(h))
  const result = {}
  normalized.forEach((h, idx) => {
    if (h.includes('机构名称')) result.groupNameCol = idx
    if (h.includes('时点融资融券余额')) result.spotBalanceCol = idx
    if (h.includes('日均融资融券余额')) result.dailyBalanceCol = idx
  })
  return result
}

const readExcel = async (file, dataType) => {
  const xlsx = await loadXlsx()
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result)
        const workbook = xlsx.read(data, { type: 'array' })

        // 营业部余额特殊处理：读取两个sheet，合并同一营业部的数据
        if (dataType === 'group_balance') {
          const merged = {} // key: group_name, value: { spot_balance, daily_balance }

          workbook.SheetNames.forEach(sheetName => {
            const sheet = workbook.Sheets[sheetName]
            const rawData = xlsx.utils.sheet_to_json(sheet, { header: 1 })
            // Excel格式：第1行=sheet标题，第2行=表头，第3行起=数据
            if (rawData.length < 3) return

            const headers = rawData[1]
            const cols = detectColumns(headers)

            // 判断sheet类型
            const normalizedSheetName = normalizeColName(sheetName)
            let balanceType = null
            if (normalizedSheetName.includes('时点') || cols.spotBalanceCol !== undefined) {
              balanceType = 'spot'
            } else if (normalizedSheetName.includes('日均') || cols.dailyBalanceCol !== undefined) {
              balanceType = 'daily'
            }

            if (!balanceType) return

            // 从第3行开始读取数据（跳过sheet标题和表头）
            for (let i = 2; i < rawData.length; i++) {
              const row = rawData[i]
              if (!row || row.length === 0) continue

              const rawGroupName = row[cols.groupNameCol] || ''
              if (!rawGroupName) continue
              if (String(rawGroupName).includes('合计')) continue
              if (String(rawGroupName).includes('查询表')) continue

              const mappedGroupName = groupNameMapping[String(rawGroupName).trim()] || String(rawGroupName).trim()

              const balanceCol = balanceType === 'spot' ? cols.spotBalanceCol : cols.dailyBalanceCol
              if (balanceCol === undefined) continue

              const rawAmount = row[balanceCol]
              if (rawAmount === undefined || rawAmount === null || rawAmount === '') continue

              // 单位为元，转换为万元
              const amountWan = parseFloat(rawAmount) / 10000

              if (!merged[mappedGroupName]) {
                merged[mappedGroupName] = { group_name: mappedGroupName, spot_balance: 0, daily_balance: 0 }
              }
              if (balanceType === 'spot') {
                merged[mappedGroupName].spot_balance = amountWan
              } else {
                merged[mappedGroupName].daily_balance = amountWan
              }
            }
          })

          resolve(Object.values(merged))
          return
        }

        // 其他类型：读取第一个sheet
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
        const jsonData = xlsx.utils.sheet_to_json(firstSheet)
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
  background: #FFF7ED; border-left: 3px solid #EA580C;
  padding: 12px 16px; border-radius: 0 8px 8px 0;
  margin-bottom: 20px; font-size: 13px; color: #9A3412;
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
  background: #FFF7ED; color: #EA580C;
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
  border-color: #EA580C;
  background: #FAFAFB;
}
.upload-icon {
  font-size: 28px; color: #EA580C; margin-bottom: 8px;
}
.upload-text {
  font-size: 13px; color: #6B7280;
}
.upload-text em {
  color: #EA580C; font-style: normal; font-weight: 500;
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
  background: #EA580C; border-color: #EA580C;
}
@media (max-width: 900px) {
  .import-grid { grid-template-columns: 1fr; }
}
</style>
