<template>
  <div class="advisory-import">
    <!-- Info Card -->
    <div class="info-card">
      <div class="info-title">
        <el-icon><InfoFilled /></el-icon>
        数据导入说明
      </div>
      <div class="info-content">
        <p><strong>时点更新机制：</strong>每次导入将根据"数据日期"全量替换该日期的所有记录。已有数据将被删除，新数据将被插入。</p>
        <p><strong>必填字段：</strong>营业部、员工姓名、签约日期、产品类型、签约资产(万)、投顾收入(元)</p>
        <p><strong>产品类型：</strong>千1、千3、万2、网格、量化T、GWT</p>
      </div>
    </div>

    <!-- Import Area -->
    <div class="import-card">
      <div class="date-selector">
        <span class="label">数据日期：</span>
        <el-date-picker
          v-model="recordDate"
          type="date"
          placeholder="选择数据日期"
          value-format="YYYY-MM-DD"
          style="width: 180px"
        />
      </div>

      <el-upload
        class="upload-area"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :limit="1"
        accept=".xlsx,.xls"
      >
        <el-icon class="upload-icon"><Upload /></el-icon>
        <div class="upload-text">
          <span>拖拽文件到此处，或</span>
          <em>点击上传</em>
        </div>
        <template #tip>
          <div class="upload-tip">
            支持 .xlsx, .xls 格式，单次导入建议不超过5000条记录
          </div>
        </template>
      </el-upload>

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
        <span class="preview-title">数据预览 (共 {{ previewData.length }} 条)</span>
        <span class="preview-valid">有效: {{ validCount }} 条</span>
      </div>
      <el-table :data="previewData.slice(0, 10)" size="small" stripe max-height="400">
        <el-table-column type="index" label="序号" width="50" />
        <el-table-column prop="group_name" label="营业部" width="120" />
        <el-table-column prop="member_name" label="员工姓名" width="100" />
        <el-table-column prop="subscription_date" label="签约日期" width="110" />
        <el-table-column prop="product_type" label="产品类型" width="90" />
        <el-table-column prop="asset_amount" label="签约资产(万)" width="110" align="right" />
        <el-table-column prop="advisory_income" label="投顾收入(元)" width="120" align="right" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.valid" type="success" size="small">有效</el-tag>
            <el-tag v-else type="danger" size="small">无效</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="previewData.length > 10" class="preview-more">
        还有 {{ previewData.length - 10 }} 条数据...
      </div>
    </div>

    <!-- Import History -->
    <div class="history-card">
      <div class="history-title">最近导入记录</div>
      <el-table :data="importHistory" size="small" stripe>
        <el-table-column prop="record_date" label="数据日期" width="120" />
        <el-table-column prop="success_count" label="成功条数" width="90" align="center" />
        <el-table-column prop="error_count" label="失败条数" width="90" align="center">
          <template #default="{ row }">
            <span :class="{ 'has-error': row.error_count > 0 }">{{ row.error_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="import_time" label="导入时间" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, InfoFilled } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { advisoryApi } from '../../api/advisory.js'
import { groupsApi, membersApi } from '../../api/index.js'

const recordDate = ref(new Date().toISOString().split('T')[0])
const importing = ref(false)
const previewData = ref([])
const groups = ref([])
const members = ref([])
const importHistory = ref([])

const productTypes = ['千1', '千3', '万2', '网格', '量化T', 'GWT']

const validCount = computed(() => previewData.value.filter(d => d.valid).length)
const canImport = computed(() => recordDate.value && validCount.value > 0)

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

const handleFileChange = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array' })
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
      const jsonData = XLSX.utils.sheet_to_json(firstSheet)

      previewData.value = parseData(jsonData)
      ElMessage.success(`解析成功，共 ${previewData.value.length} 条数据`)
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

const parseData = (rawData) => {
  const groupMap = {}
  const memberMap = {}

  groups.value.forEach(g => {
    groupMap[g.name] = g.id
    groupMap[g.name.replace(/\s/g, '')] = g.id
  })

  members.value.forEach(m => {
    memberMap[m.name] = m
    memberMap[m.name.replace(/\s/g, '')] = m
  })

  return rawData.map((row, index) => {
    const groupName = row['营业部'] || row['部门'] || ''
    const memberName = row['员工姓名'] || row['姓名'] || ''
    const productType = row['产品类型'] || row['产品'] || ''
    const subscriptionDate = row['签约日期'] || row['日期'] || ''
    const assetAmount = parseFloat(row['签约资产(万)'] || row['资产'] || row['签约资产'] || 0)
    const advisoryIncome = parseFloat(row['投顾收入(元)'] || row['收入'] || row['投顾收入'] || 0)

    const group = groupMap[groupName]
    const member = memberMap[memberName]
    const validProduct = productTypes.includes(productType)

    const errors = []
    if (!group) errors.push('营业部不存在')
    if (!member) errors.push('员工不存在')
    if (!validProduct) errors.push('产品类型无效')
    if (!subscriptionDate) errors.push('缺少签约日期')
    if (assetAmount <= 0) errors.push('资产必须大于0')

    return {
      row_num: index + 1,
      group_id: group,
      group_name: groupName,
      member_id: member?.id,
      member_name: memberName,
      product_type: productType,
      subscription_date: formatDate(subscriptionDate),
      asset_amount: assetAmount,
      advisory_income: advisoryIncome,
      valid: errors.length === 0,
      errors
    }
  })
}

const formatDate = (dateValue) => {
  if (!dateValue) return null
  if (typeof dateValue === 'number') {
    const date = XLSX.SSF.parse_date_code(dateValue)
    return `${date.y}-${String(date.m).padStart(2, '0')}-${String(date.d).padStart(2, '0')}`
  }
  const str = String(dateValue)
  if (str.includes('-')) return str
  if (str.includes('/')) {
    const parts = str.split('/')
    return `${parts[0]}-${String(parts[1]).padStart(2, '0')}-${String(parts[2]).padStart(2, '0')}`
  }
  return str
}

const handleImport = async () => {
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
      `确定要导入 ${validData.length} 条记录吗？\n数据日期：${recordDate.value}\n\n注意：该日期的现有数据将被替换。`,
      '确认导入',
      { type: 'warning' }
    )
  } catch {
    return
  }

  importing.value = true
  try {
    const importData = validData.map(d => ({
      member_name: d.member_name,
      group_name: d.group_name,
      product_type: d.product_type,
      subscription_date: d.subscription_date,
      asset_amount: d.asset_amount,
      advisory_income: d.advisory_income
    }))

    const res = await advisoryApi.importSubscriptions({
      record_date: recordDate.value,
      data: importData
    })

    importHistory.value.unshift({
      record_date: recordDate.value,
      success_count: res.success_count || validData.length,
      error_count: res.errors?.length || 0,
      import_time: new Date().toLocaleString()
    })

    ElMessage.success(`导入成功：${res.success_count || validData.length} 条`)
    previewData.value = []
  } catch (error) {
    console.error('Import error:', error)
    ElMessage.error(error.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

const downloadTemplate = () => {
  const template = [{
    '营业部': '示例营业部',
    '员工姓名': '张三',
    '签约日期': '2026-04-15',
    '产品类型': '千1',
    '签约资产(万)': 100,
    '投顾收入(元)': 1000
  }]

  const ws = XLSX.utils.json_to_sheet(template)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '导入模板')

  // Set column widths
  ws['!cols'] = [
    { wch: 15 }, { wch: 12 }, { wch: 12 }, { wch: 10 }, { wch: 15 }, { wch: 15 }
  ]

  XLSX.writeFile(wb, '投顾签约导入模板.xlsx')
}

onMounted(() => {
  fetchGroups()
  fetchMembers()
})
</script>

<style scoped>
.advisory-import {
  padding: 0;
}

.info-card {
  background: linear-gradient(135deg, #ECFEFF 0%, #E0F2FE 100%);
  border: 1px solid #A5F3FC;
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
  color: #0E7490;
  margin-bottom: 12px;
}

.info-content {
  font-size: 13px;
  color: #0F766E;
  line-height: 1.8;
}

.info-content p {
  margin: 4px 0;
}

.import-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #E5E7EB;
  margin-bottom: 20px;
}

.date-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.date-selector .label {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
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
  border-color: #0891B2;
  background: #F0FDFA;
}

.upload-icon {
  font-size: 48px;
  color: #9CA3AF;
  margin-bottom: 16px;
}

.upload-text {
  font-size: 14px;
  color: #6B7280;
}

.upload-text em {
  color: #0891B2;
  font-style: normal;
  font-weight: 500;
  margin-left: 4px;
}

.upload-tip {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 8px;
  text-align: center;
}

.import-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
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
}

.preview-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.preview-valid {
  font-size: 14px;
  color: #10B981;
  font-weight: 500;
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
  padding: 20px;
  border: 1px solid #E5E7EB;
}

.history-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16px;
}

.has-error {
  color: #EF4444;
  font-weight: 600;
}
</style>
