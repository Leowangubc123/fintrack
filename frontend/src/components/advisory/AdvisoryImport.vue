<template>
  <div class="advisory-import">
    <!-- Info Card -->
    <div class="info-card">
      <div class="info-title">
        <el-icon><InfoFilled /></el-icon>
        数据导入说明
      </div>
      <div class="info-content">
        <p><strong>产品数据导入：</strong>选择产品类型（万2、千1、千3、ETF投顾、量化T策略、GWT），上传该产品对应的Excel表格。</p>
        <p><strong>收入数据导入：</strong>选择"投顾收入"类型，上传各营业部收入汇总表。</p>
        <p><strong>更新机制：</strong>每次导入只会更新选定产品/收入类型的数据，其他数据不受影响。</p>
        <p><strong>必填字段：</strong></p>
        <ul>
          <li>产品数据：营业部、认领员工、订购日期(YYYYMMDD)、订单状态、昨日净资产</li>
          <li>收入数据：营业部、投顾收入(元)</li>
        </ul>
      </div>
    </div>

    <!-- Import Area -->
    <div class="import-card">
      <!-- Step 1: Select Product Type -->
      <div class="step-section">
        <div class="step-label">步骤 1：选择数据类型</div>
        <el-select v-model="selectedProductType" placeholder="请选择数据类型" style="width: 240px">
          <el-option-group label="产品签约数据">
            <el-option v-for="type in productTypes" :key="type" :label="type" :value="type" />
          </el-option-group>
          <el-option-group label="收入数据">
            <el-option label="投顾收入" value="投顾收入" />
          </el-option-group>
        </el-select>
      </div>

      <!-- Step 2: Select Date -->
      <div class="step-section">
        <div class="step-label">步骤 2：选择数据日期</div>
        <el-date-picker
          v-model="recordDate"
          type="date"
          placeholder="选择数据日期"
          value-format="YYYY-MM-DD"
          style="width: 180px"
        />
      </div>

      <!-- Step 3: Upload File -->
      <div class="step-section">
        <div class="step-label">步骤 3：上传Excel文件</div>
        <el-upload
          class="upload-area"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          :limit="1"
          accept=".xlsx,.xls"
          :disabled="!selectedProductType"
        >
          <el-icon class="upload-icon"><Upload /></el-icon>
          <div class="upload-text">
            <span v-if="selectedProductType">拖拽文件到此处，或<em>点击上传</em></span>
            <span v-else>请先选择数据类型</span>
          </div>
          <template #tip>
            <div class="upload-tip">
              支持 .xlsx, .xls 格式
              <span v-if="selectedProductType === '投顾收入'"> - 需包含"营业部"和"投顾收入"列</span>
              <span v-else-if="selectedProductType"> - 需包含"营业部"、"认领员工"、"订购日期"、"订单状态"、"昨日净资产"列</span>
            </div>
          </template>
        </el-upload>
      </div>

      <div class="import-actions">
        <el-button
          type="primary"
          size="large"
          :disabled="!canImport"
          :loading="importing"
          @click="handleImport"
        >
          <el-icon><Upload /></el-icon>
          开始导入
        </el-button>
        <el-button size="large" @click="downloadTemplate">下载模板</el-button>
      </div>
    </div>

    <!-- Preview Table -->
    <div v-if="previewData.length > 0" class="preview-card">
      <div class="preview-header">
        <span class="preview-title">
          数据预览 - {{ selectedProductType }} (共 {{ previewData.length }} 条)
        </span>
        <div class="preview-stats">
          <span class="stat-item">有效: {{ validCount }} 条</span>
          <span class="stat-item" v-if="skippedCount > 0">跳过(非支付成功): {{ skippedCount }} 条</span>
          <span class="stat-item error" v-if="errorCount > 0">错误: {{ errorCount }} 条</span>
        </div>
      </div>

      <!-- Product Data Preview -->
      <el-table v-if="selectedProductType !== '投顾收入'" :data="previewData" size="small" stripe max-height="600">
        <el-table-column type="index" label="序号" width="50" />
        <el-table-column prop="group_name" label="营业部" width="120" />
        <el-table-column prop="member_name" label="认领员工" width="100" />
        <el-table-column prop="subscription_date" label="订购日期" width="110" />
        <el-table-column prop="order_status" label="订单状态" width="90" />
        <el-table-column prop="asset_amount" label="昨日净资产(万)" width="120" align="right">
          <template #default="{ row }">{{ (row.asset_amount / 10000).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="状态" min-width="180">
          <template #default="{ row }">
            <el-tag v-if="row.valid && !row.skipped" type="success" size="small">有效</el-tag>
            <el-tag v-else-if="row.skipped" type="info" size="small">跳过</el-tag>
            <el-tooltip v-else :content="row.error" placement="top" :show-after="200">
              <el-tag type="danger" size="small" style="max-width: 100%">{{ row.error }}</el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <!-- Income Data Preview -->
      <el-table v-else :data="previewData" size="small" stripe max-height="600">
        <el-table-column type="index" label="序号" width="50" />
        <el-table-column prop="group_name" label="营业部" width="200" />
        <el-table-column prop="advisory_income" label="投顾收入(元)" width="150" align="right" />
        <el-table-column label="状态" min-width="180">
          <template #default="{ row }">
            <el-tag v-if="row.valid" type="success" size="small">有效</el-tag>
            <el-tooltip v-else :content="row.error" placement="top" :show-after="200">
              <el-tag type="danger" size="small" style="max-width: 100%">{{ row.error }}</el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Import History -->
    <div class="history-card">
      <div class="history-title">最近导入记录</div>
      <el-table :data="importHistory" size="small" stripe>
        <el-table-column prop="import_date" label="数据日期" width="120" />
        <el-table-column prop="product_type" label="数据类型" width="120" />
        <el-table-column prop="record_count" label="总条数" width="80" align="center" />
        <el-table-column prop="success_count" label="成功" width="70" align="center" />
        <el-table-column prop="error_count" label="失败" width="70" align="center">
          <template #default="{ row }">
            <span :class="{ 'has-error': row.error_count > 0 }">{{ row.error_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人" width="100" />
        <el-table-column prop="created_at" label="导入时间" min-width="150">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Latest Update Times -->
    <div class="history-card latest-update-card">
      <div class="history-title">各数据类型最新更新时间</div>
      <el-table :data="latestUpdates" size="small" stripe>
        <el-table-column prop="product_type" label="数据类型" width="120" />
        <el-table-column prop="import_date" label="数据日期" width="120" />
        <el-table-column prop="created_at" label="最新导入时间" min-width="150">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人" width="100" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, InfoFilled } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { advisoryApi } from '../../api/advisory.js'
import { groupsApi, membersApi } from '../../api/index.js'

const productTypes = ['万2', '千1', '千3', 'ETF投顾', '量化T策略', 'GWT']
const selectedProductType = ref('')
const recordDate = ref(new Date().toISOString().split('T')[0])
const importing = ref(false)
const previewData = ref([])
const groups = ref([])
const members = ref([])
const importHistory = ref([])

const validCount = computed(() => previewData.value.filter(d => d.valid).length)
const skippedCount = computed(() => previewData.value.filter(d => d.skipped).length)
const errorCount = computed(() => previewData.value.filter(d => !d.valid && !d.skipped).length)
const canImport = computed(() => selectedProductType.value && recordDate.value && validCount.value > 0)

const latestUpdates = computed(() => {
  const map = new Map()
  importHistory.value.forEach(log => {
    if (!map.has(log.product_type)) {
      map.set(log.product_type, log)
    }
  })
  return Array.from(map.values())
})

const fetchGroups = async () => {
  try {
    const res = await groupsApi.list()
    groups.value = res
  } catch (error) {
    console.error('Failed to fetch groups:', error)
  }
}

const fetchMembers = async () => {
  try {
    const res = await membersApi.getAll()
    members.value = res
  } catch (error) {
    console.error('Failed to fetch members:', error)
  }
}

const fetchImportHistory = async () => {
  try {
    const res = await advisoryApi.getImportLogs(20)
    importHistory.value = res
  } catch (error) {
    console.error('Failed to fetch import logs:', error)
  }
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const handleFileChange = (file) => {
  if (!selectedProductType.value) {
    ElMessage.warning('请先选择数据类型')
    return
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array' })
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
      const jsonData = XLSX.utils.sheet_to_json(firstSheet)

      if (selectedProductType.value === '投顾收入') {
        previewData.value = parseIncomeData(jsonData)
      } else {
        previewData.value = parseProductData(jsonData)
      }

      const valid = previewData.value.filter(d => d.valid).length
      const skipped = previewData.value.filter(d => d.skipped).length
      ElMessage.success(`解析成功，有效 ${valid} 条${skipped > 0 ? `，跳过 ${skipped} 条` : ''}`)
    } catch (error) {
      console.error('Parse error:', error)
      ElMessage.error('文件解析失败，请检查文件格式')
    }
  }
  reader.readAsArrayBuffer(file.raw)
}

const handleFileRemove = () => {
  previewData.value = []
}

// Parse product subscription data
const parseProductData = (rawData) => {
  const groupMap = {}
  const memberMap = {}

  groups.value.forEach(g => {
    groupMap[g.name] = g
    groupMap[g.name.replace(/\s/g, '')] = g
  })

  members.value.forEach(m => {
    memberMap[m.name] = m
    memberMap[m.name.replace(/\s/g, '')] = m
  })

  return rawData.map((row, index) => {
    // Extract fields from various possible column names
    const groupName = row['营业部'] || row['部门'] || ''
    const memberName = row['认领员工'] || row['员工'] || row['员工姓名'] || ''
    const orderDateRaw = row['订购日期'] || row['日期'] || row['签约日期'] || ''
    const orderStatus = row['订单状态'] || row['状态'] || ''
    const assetAmount = row['昨日净资产'] || row['资产'] || row['签约资产'] || 0

    const group = groupMap[groupName]
    const member = memberMap[memberName]

    // Check if order status is valid
    if (orderStatus !== '支付成功') {
      return {
        row_num: index + 1,
        group_name: groupName,
        member_name: memberName,
        subscription_date: parseDate(orderDateRaw),
        order_status: orderStatus || '未知',
        asset_amount: parseFloat(assetAmount) || 0,
        valid: false,
        skipped: true,
        error: '非支付成功'
      }
    }

    // Validate required fields
    if (!memberName || !member) {
      return {
        row_num: index + 1,
        group_name: groupName,
        member_name: memberName || '(空白)',
        subscription_date: parseDate(orderDateRaw),
        order_status: orderStatus,
        asset_amount: parseFloat(assetAmount) || 0,
        valid: false,
        skipped: false,
        error: !memberName ? '缺少认领员工' : `未找到员工: ${memberName}`
      }
    }

    if (!group) {
      return {
        row_num: index + 1,
        group_name: groupName || '(空白)',
        member_name: memberName,
        subscription_date: parseDate(orderDateRaw),
        order_status: orderStatus,
        asset_amount: parseFloat(assetAmount) || 0,
        valid: false,
        skipped: false,
        error: !groupName ? '缺少营业部' : `未找到营业部: ${groupName}`
      }
    }

    return {
      row_num: index + 1,
      group_id: group.id,
      group_name: group.name,
      member_id: member.id,
      member_name: member.name,
      subscription_date: parseDate(orderDateRaw),
      order_status: orderStatus,
      asset_amount: parseFloat(assetAmount) || 0,
      valid: true,
      skipped: false,
      error: null
    }
  })
}

// Parse income data
const parseIncomeData = (rawData) => {
  const groupMap = {}

  groups.value.forEach(g => {
    groupMap[g.name] = g
    groupMap[g.name.replace(/\s/g, '')] = g
  })

  return rawData.map((row, index) => {
    const groupName = row['营业部'] || row['部门'] || ''
    const incomeValue = row['投顾收入'] || row['收入'] || 0

    const group = groupMap[groupName]

    if (!group) {
      return {
        row_num: index + 1,
        group_name: groupName || '(空白)',
        advisory_income: parseFloat(incomeValue) || 0,
        valid: false,
        error: !groupName ? '缺少营业部' : `未找到营业部: ${groupName}`
      }
    }

    return {
      row_num: index + 1,
      group_id: group.id,
      group_name: group.name,
      advisory_income: parseFloat(incomeValue) || 0,
      valid: true,
      error: null
    }
  })
}

// Parse date from YYYYMMDD format
const parseDate = (dateValue) => {
  if (!dateValue) return null

  try {
    let dateStr = String(dateValue).replace(/[-/]/g, '')

    // Handle Excel date serial number
    if (typeof dateValue === 'number' && dateValue > 30000) {
      const date = XLSX.SSF.parse_date_code(dateValue)
      return `${date.y}-${String(date.m).padStart(2, '0')}-${String(date.d).padStart(2, '0')}`
    }

    // Parse YYYYMMDD
    if (dateStr.length === 8) {
      return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`
    }

    // Try to parse as date string
    const d = new Date(dateValue)
    if (!isNaN(d.getTime())) {
      return d.toISOString().split('T')[0]
    }

    return dateStr
  } catch (e) {
    return String(dateValue)
  }
}

const handleImport = async () => {
  if (!selectedProductType.value) {
    ElMessage.warning('请选择数据类型')
    return
  }

  if (!recordDate.value) {
    ElMessage.warning('请选择数据日期')
    return
  }

  const validData = previewData.value.filter(d => d.valid)
  if (validData.length === 0) {
    ElMessage.warning('没有有效的数据可导入')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要导入 ${validData.length} 条 ${selectedProductType.value} 数据吗？\n数据日期：${recordDate.value}`,
      '确认导入',
      { type: 'warning' }
    )
  } catch {
    return
  }

  importing.value = true
  try {
    const res = await advisoryApi.importSubscriptions({
      record_date: recordDate.value,
      product_type: selectedProductType.value,
      data: validData
    })

    ElMessage.success(`导入成功：${res.success_count} 条${res.error_count > 0 ? `，失败 ${res.error_count} 条` : ''}`)
    previewData.value = []
    fetchImportHistory()
  } catch (error) {
    console.error('Import error:', error)
    ElMessage.error(error.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

const downloadTemplate = () => {
  if (!selectedProductType.value) {
    ElMessage.warning('请先选择数据类型以下载对应模板')
    return
  }

  let template, filename, ws
  const wb = XLSX.utils.book_new()

  if (selectedProductType.value === '投顾收入') {
    template = [{
      '营业部': '示例营业部',
      '投顾收入': 50000
    }]
    filename = '投顾收入导入模板.xlsx'
    ws = XLSX.utils.json_to_sheet(template)
    ws['!cols'] = [{ wch: 20 }, { wch: 15 }]
  } else {
    template = [{
      '营业部': '示例营业部',
      '认领员工': '张三',
      '订购日期': '20260101',
      '订单状态': '支付成功',
      '昨日净资产': 1000000
    }]
    filename = `${selectedProductType.value}导入模板.xlsx`
    ws = XLSX.utils.json_to_sheet(template)
    ws['!cols'] = [
      { wch: 15 }, { wch: 12 }, { wch: 12 }, { wch: 10 }, { wch: 15 }
    ]
  }

  XLSX.utils.book_append_sheet(wb, ws, '导入模板')
  XLSX.writeFile(wb, filename)
}

watch(selectedProductType, () => {
  previewData.value = []
})

onMounted(() => {
  fetchGroups()
  fetchMembers()
  fetchImportHistory()
})
</script>

<style scoped>
.advisory-import {
  padding: 0;
}

.info-card {
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
  border: 1px solid #BFDBFE;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.info-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1EAEDB;
  margin-bottom: 12px;
}

.info-content {
  font-size: 13px;
  color: #1E40AF;
  line-height: 1.8;
}

.info-content p {
  margin: 4px 0;
}

.info-content ul {
  margin: 4px 0;
  padding-left: 20px;
}

.info-content li {
  margin: 2px 0;
}

.import-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #E5E7EB;
  margin-bottom: 20px;
}

.step-section {
  margin-bottom: 20px;
}

.step-section:last-child {
  margin-bottom: 0;
}

.step-label {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #FAFAFB;
  border: 2px dashed #D1D5DB;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: #1EAEDB;
  background: #EFF6FF;
}

.upload-area :deep(.el-upload-dragger.is-disabled) {
  background: #F3F4F6;
  border-color: #E5E7EB;
  cursor: not-allowed;
}

.upload-icon {
  font-size: 48px;
  color: #9CA3AF;
  margin-bottom: 16px;
}

.upload-text {
  font-size: 14px;
  color: #374151;
}

.upload-text em {
  color: #1EAEDB;
  font-style: normal;
  font-weight: 500;
  margin-left: 4px;
}

.upload-tip {
  font-size: 12px;
  color: #6B7280;
  margin-top: 8px;
  text-align: center;
}

.import-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
}

.import-actions :deep(.el-button--primary) {
  background: #1EAEDB;
  border-color: #1EAEDB;
}

.preview-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #E5E7EB;
  margin-bottom: 20px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.preview-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  font-size: 14px;
  color: #10B981;
  font-weight: 500;
}

.stat-item.error {
  color: #EF4444;
}

.preview-more {
  text-align: center;
  padding: 12px;
  color: #9CA3AF;
  font-size: 13px;
}

.history-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #E5E7EB;
}

.history-card.latest-update-card {
  margin-top: 20px;
}

.history-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 20px;
}

/* Table styling improvements */
.history-card :deep(.el-table) {
  font-size: 14px;
}

.history-card :deep(.el-table th) {
  background: #F9FAFB;
  font-weight: 600;
  color: #374151;
  font-size: 13px;
  padding: 12px 0;
}

.history-card :deep(.el-table td) {
  color: #111827;
  padding: 14px 0;
  font-size: 14px;
}

.history-card :deep(.el-table__row) {
  transition: background 0.15s ease;
}

.history-card :deep(.el-table__row:hover td) {
  background: #F8FAFC;
}

.has-error {
  color: #EF4444;
  font-weight: 600;
}
</style>