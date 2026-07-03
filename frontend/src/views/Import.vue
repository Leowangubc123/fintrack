<template>
  <div class="import-page">
    <div class="import-wizard">
      <!-- 5步向导 -->
      <div class="wizard-steps">
        <div
          v-for="(step, index) in steps"
          :key="index"
          class="wizard-step"
          :class="{ active: currentStep === index, completed: currentStep > index }"
        >
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-label">{{ step }}</div>
        </div>
      </div>

      <!-- 步骤内容 -->
      <div class="wizard-content">
        <!-- 步骤1: 选择产品 -->
        <div v-if="currentStep === 0" class="wizard-step-content active">
          <div class="step-title">选择要导入数据的产品</div>
          <div class="step-desc">请选择本次导入数据关联的基金产品</div>
          <div class="product-select-grid">
            <div
              v-for="product in products"
              :key="product.id"
              class="product-select-item"
              :class="{ selected: selectedProduct === product.id }"
              @click="selectedProduct = product.id"
            >
              <div style="font-weight: 600; color: #1D1D1F; margin-bottom: 4px;">
                {{ product.name }}
              </div>
              <div style="font-size: 13px; color: #6E6E73;">
                {{ product.issuer }} | {{ product.code }}
              </div>
            </div>
          </div>
          <div class="wizard-actions">
            <el-button @click="$router.back()">取消</el-button>
            <el-button type="primary" @click="nextStep" :disabled="!selectedProduct">
              下一步
            </el-button>
          </div>
        </div>

        <!-- 步骤2: 上传文件 -->
        <div v-if="currentStep === 1" class="wizard-step-content active">
          <div class="step-title">上传Excel文件</div>
          <div class="step-desc">支持 .xlsx, .xls, .csv 格式，文件大小不超过 10MB</div>
          <div v-if="selectedProductInfo" class="selected-product-info">
            <div class="selected-product-label">当前导入产品</div>
            <div class="selected-product-name">{{ selectedProductInfo.name }}</div>
            <div class="selected-product-code">{{ selectedProductInfo.issuer }} | {{ selectedProductInfo.code }}</div>
          </div>
          <el-upload
            class="upload-area"
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            accept=".xlsx,.xls,.csv"
          >
            <el-icon :size="48" style="color: #007AFF; margin-bottom: 16px;">
              <Upload />
            </el-icon>
            <div class="upload-text">点击或拖拽文件到此处上传</div>
            <div class="upload-hint">支持 .xlsx, .xls, .csv 格式</div>
          </el-upload>
          <div class="template-download">
            <el-button link type="primary" @click="downloadTemplate">
              <el-icon><Download /></el-icon>
              下载导入模板
            </el-button>
            <span class="template-tip">请使用标准模板格式导入数据</span>
          </div>
          <div class="wizard-actions">
            <el-button @click="prevStep">上一步</el-button>
            <el-button
              type="primary"
              @click="uploadFile"
              :loading="uploading"
              :disabled="!uploadFileRaw"
            >
              下一步
            </el-button>
          </div>
        </div>

        <!-- 步骤3: 字段映射 -->
        <div v-if="currentStep === 2" class="wizard-step-content active">
          <div class="step-title">字段映射确认</div>
          <div class="step-desc">系统已自动识别Excel列与系统字段的映射关系，请确认是否正确</div>
          <div v-if="selectedProductInfo" class="selected-product-info">
            <div class="selected-product-label">当前导入产品</div>
            <div class="selected-product-name">{{ selectedProductInfo.name }}</div>
            <div class="selected-product-code">{{ selectedProductInfo.issuer }} | {{ selectedProductInfo.code }}</div>
          </div>

          <!-- 证券代码校验提示 -->
          <div v-if="codeValidationResult" class="validation-result" :class="{ error: !codeValidationResult.match }">
            <div class="validation-title">
              <el-icon><Check v-if="codeValidationResult.match" /><Close v-else /></el-icon>
              {{ codeValidationResult.match ? '证券代码校验通过' : '证券代码不匹配！' }}
            </div>
            <div style="font-size: 13px; color: #6E6E73; margin-top: 4px;">
              所选产品代码：<strong>{{ selectedProductInfo?.code }}</strong>
              <span v-if="codeValidationResult.foundCodes.length">
                · Excel中的证券代码：<strong>{{ codeValidationResult.foundCodes.join(', ') }}</strong>
              </span>
            </div>
            <div v-if="!codeValidationResult.match" style="font-size: 12px; color: #DC2626; margin-top: 4px;">
              请检查您选择的产品是否与上传的Excel数据匹配，避免错误导入。
            </div>
          </div>

          <div class="validation-result">
            <div class="validation-title">
              <el-icon><Check /></el-icon>
              自动映射成功
            </div>
            <ul class="validation-list">
              <li v-for="mapping in columnMapping" :key="mapping.systemField">
                {{ mapping.systemField }} → {{ mapping.excelColumn }}
              </li>
            </ul>
          </div>

          <div v-if="rowFilterStats.skipped > 0" class="validation-result" style="background: #FEF3C7;">
            <div class="validation-title" style="color: #92400E;">
              <el-icon><InfoFilled /></el-icon>
              数据过滤说明
            </div>
            <div style="font-size: 13px; color: #92400E; margin-top: 4px;">
              共 {{ rowFilterStats.total }} 行数据，
              其中 <strong>{{ rowFilterStats.valid }}</strong> 行有效，
              <strong>{{ rowFilterStats.skipped }}</strong> 行被过滤
              （销售人员为空或委托数量为0）
            </div>
          </div>

          <!-- 营业部映射统计 -->
          <div class="validation-result" style="background: #E0F2FE;">
            <div class="validation-title" style="color: #0369A1;">
              <el-icon><Check /></el-icon>
              营业部自动映射完成
            </div>
            <div style="font-size: 13px; color: #0369A1; margin-top: 4px;">
              系统已根据销售人员姓名自动匹配所属营业部
              <span v-if="previewData.length > 0">
                · 共匹配 <strong>{{ previewUniqueMembers }}</strong> 位销售人员，
                分布在 <strong>{{ previewUniqueGroups }}</strong> 个营业部
              </span>
            </div>
          </div>

          <div class="wizard-actions">
            <el-button @click="prevStep">上一步</el-button>
            <el-button type="primary" @click="loadPreviewData" :disabled="codeValidationResult && !codeValidationResult.match">下一步</el-button>
          </div>
        </div>

        <!-- 步骤4: 数据预览 -->
        <div v-if="currentStep === 3" class="wizard-step-content active">
          <div class="step-title">数据预览</div>
          <div class="step-desc">共 {{ previewData.length }} 条数据，请检查是否正确</div>

          <!-- 汇总统计 -->
          <div class="summary-stats-bar">
            <div class="summary-stat-item">
              <div class="summary-stat-label">本次上传汇总销量</div>
              <div class="summary-stat-value">{{ previewTotalAmount }} <span class="summary-unit">万元</span></div>
            </div>
            <div class="summary-stat-divider"></div>
            <div class="summary-stat-item">
              <div class="summary-stat-label">销售人员数</div>
              <div class="summary-stat-value">{{ previewUniqueMembers }} <span class="summary-unit">人</span></div>
            </div>
            <div class="summary-stat-divider"></div>
            <div class="summary-stat-item">
              <div class="summary-stat-label">人均销量</div>
              <div class="summary-stat-value">{{ previewAvgAmount }} <span class="summary-unit">万元</span></div>
            </div>
          </div>
          <div v-if="selectedProductInfo" class="selected-product-info">
            <div class="selected-product-label">当前导入产品</div>
            <div class="selected-product-name">{{ selectedProductInfo.name }}</div>
            <div class="selected-product-code">{{ selectedProductInfo.issuer }} | {{ selectedProductInfo.code }}</div>
          </div>
          <div class="preview-table-container">
            <el-table :data="previewData" height="350">
              <el-table-column type="index" label="序号" width="60" />
              <el-table-column prop="销售人员" label="销售人员" />
              <el-table-column prop="所属营业部" label="所属营业部" />
              <el-table-column prop="销售金额" label="销售金额" />
              <el-table-column prop="交易日期" label="交易日期" />
              <el-table-column prop="备注" label="备注" />
            </el-table>
          </div>
          <div class="wizard-actions">
            <el-button @click="prevStep">上一步</el-button>
            <el-button type="primary" @click="executeImport" :loading="importing">确认导入</el-button>
          </div>
        </div>

        <!-- 步骤5: 完成导入 -->
        <div v-if="currentStep === 4" class="wizard-step-content active">
          <div v-if="importResult && importResult.failed > 0" class="success-check" style="text-align: left;">
            <div class="success-icon" style="background: #F59E0B;">!</div>
            <div class="success-title" style="color: #92400E;">导入完成，但有失败记录</div>
            <div class="success-desc">
              成功 {{ importResult.success }} 条，失败 {{ importResult.failed }} 条
            </div>
            <div v-if="importResult.errors && importResult.errors.length" class="error-list" style="max-height: 300px; overflow-y: auto; margin: 16px 0; text-align: left;">
              <div v-for="(err, idx) in importResult.errors" :key="idx" class="error-item" style="padding: 8px 12px; margin-bottom: 8px; background: #FEF3C7; border-radius: 8px; color: #92400E; font-size: 13px;">
                <strong>第 {{ err.row }} 行：</strong>{{ err.error }}
                <span v-if="err.member_name" style="color: #78350F;">（{{ err.member_name }}）</span>
              </div>
            </div>
            <el-button type="primary" @click="resetWizard">完成</el-button>
          </div>
          <div v-else class="success-check">
            <div class="success-icon">✓</div>
            <div class="success-title">导入成功！</div>
            <div class="success-desc">
              成功导入 {{ previewData.length }} 条销售记录到产品 <strong v-if="selectedProductInfo">{{ selectedProductInfo.name }} ({{ selectedProductInfo.code }})</strong>
            </div>
            <el-button type="primary" @click="resetWizard">完成</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { productsApi, importApi } from '../api'
import { groupsApi, membersApi } from '../api/index.js'
import { Upload, Check, Download, Close, InfoFilled } from '@element-plus/icons-vue'

const currentStep = ref(0)
const selectedProduct = ref(null)
const products = ref([])
const groups = ref([])
const existingMembers = ref([])

// 成员名称 → 营业部名称 的映射（用于预览显示）
const memberGroupMap = computed(() => {
  const map = {}
  existingMembers.value.forEach(m => {
    const group = groups.value.find(g => g.id === m.group_id)
    map[m.name] = group?.name || '-'
  })
  return map
})

// 获取选中的产品信息
const selectedProductInfo = computed(() => {
  return products.value.find(p => p.id === selectedProduct.value)
})
const uploadFileRaw = ref(null)
const uploading = ref(false)
const importing = ref(false)
const previewData = ref([])
const importResult = ref(null)

// 预览数据汇总统计
const previewTotalAmount = computed(() => {
  const total = previewData.value.reduce((sum, row) => sum + (parseFloat(row['销售金额']) || 0), 0)
  return total.toFixed(2)
})

const previewUniqueMembers = computed(() => {
  const members = new Set(previewData.value.map(row => row['销售人员']).filter(Boolean))
  return members.size
})

const previewUniqueGroups = computed(() => {
  const groups = new Set(previewData.value.map(row => row['所属营业部']).filter(g => g && g !== '未匹配' && g !== '未知营业部'))
  return groups.size
})

const previewAvgAmount = computed(() => {
  const total = previewData.value.reduce((sum, row) => sum + (parseFloat(row['销售金额']) || 0), 0)
  const count = previewUniqueMembers.value
  return count > 0 ? (total / count).toFixed(2) : '0.00'
})

const steps = ['选择产品', '上传文件', '字段映射', '数据预览', '完成']

// 字段映射配置（根据实际Excel表头）
const columnMapping = ref([
  { systemField: '销售人员', excelColumn: '开发人员 / 服务人员', matched: true },
  { systemField: '销售金额', excelColumn: '委托数量 / 买入（元→万元）', matched: true },
  { systemField: '交易日期', excelColumn: '委托日期', matched: true },
])

// 证券代码验证结果
const codeValidationResult = ref(null)
// 数据过滤统计
const rowFilterStats = ref({ total: 0, valid: 0, skipped: 0 })

onMounted(() => {
  loadProducts()
  loadGroups()
})

async function loadProducts() {
  try {
    const res = await productsApi.list()
    // 只显示未归档的产品
    products.value = res.filter(p => !p.is_archived)
  } catch (error) {
    console.error('加载产品失败:', error)
  }
}

async function loadGroups() {
  try {
    const res = await groupsApi.list()
    groups.value = res
  } catch (error) {
    console.error('加载营业部失败:', error)
  }
}

function handleFileChange(file) {
  uploadFileRaw.value = file.raw
}

// 获取单元格值（处理空值）
function getCellValue(row, keys) {
  for (const key of keys) {
    if (row[key] !== undefined && row[key] !== null && String(row[key]).trim() !== '') {
      return String(row[key]).trim()
    }
  }
  return ''
}

// 格式化委托日期：YYYYMMDD → YYYY-MM-DD
function formatSaleDate(dateStr) {
  if (!dateStr || dateStr === '') return ''
  const s = String(dateStr).trim()
  // 如果已经是 YYYY-MM-DD 格式，直接返回
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s
  // 如果是 YYYYMMDD 格式，转换为 YYYY-MM-DD
  if (/^\d{8}$/.test(s)) {
    return `${s.substring(0, 4)}-${s.substring(4, 6)}-${s.substring(6, 8)}`
  }
  return s
}

// 解析委托数量（元 → 万元）
function parseAmount(amountVal) {
  if (amountVal === undefined || amountVal === null || amountVal === '') return 0
  const s = String(amountVal).replace(/,/g, '').trim()
  const num = parseFloat(s)
  if (isNaN(num)) return 0
  // 委托数量单位是元，转换为万元
  return num / 10000
}

async function uploadFile() {
  if (!uploadFileRaw.value) return
  uploading.value = true
  try {
    console.log('[DEBUG] Uploading file:', uploadFileRaw.value.name, 'size:', uploadFileRaw.value.size)
    console.log('[DEBUG] Selected product:', selectedProduct.value)
    const res = await importApi.preview(selectedProduct.value, uploadFileRaw.value)
    const rawPreview = res.preview || []

    // 保存成员数据用于营业部映射
    existingMembers.value = res.existing_members || []

    // ========== 证券代码验证 ==========
    const productCode = selectedProductInfo.value?.code
    const codeKeys = ['证券代码', '产品代码', '基金代码', '代码']
    const foundCodes = new Set()
    let codeMismatch = false

    rawPreview.forEach((row, idx) => {
      const code = getCellValue(row, codeKeys)
      if (code && code !== '' && code !== 'None') {
        foundCodes.add(code)
        // 去掉前导零后比较
        const normalizedCode = code.replace(/^0+/, '') || code
        const normalizedProductCode = productCode ? productCode.replace(/^0+/, '') : ''
        if (normalizedCode !== normalizedProductCode) {
          codeMismatch = true
          console.warn(`[IMPORT] Row ${idx + 1}: 证券代码不匹配: ${code} vs ${productCode}`)
        }
      }
    })

    codeValidationResult.value = {
      match: !codeMismatch && foundCodes.size > 0,
      foundCodes: Array.from(foundCodes),
      productCode
    }

    // ========== 字段映射（新的系统导出格式）==========
    let totalRows = 0
    let validRows = 0
    let skippedRows = 0

    const mappedData = rawPreview.map((row, idx) => {
      totalRows++

      // 1. 销售人员：开发人员优先，没有则用服务人员
      const devPerson = getCellValue(row, ['开发人员'])
      const svcPerson = getCellValue(row, ['服务人员'])
      const salesPerson = devPerson || svcPerson

      // 2. 销售金额：委托数量（元 → 万元）
      const amount = parseAmount(getCellValue(row, ['委托数量', '买入', '认购金额', '金额', '成交数量']))

      // 3. 交易日期：委托日期/交易日期/销售日期
      const saleDate = formatSaleDate(getCellValue(row, ['委托日期', '交易日期', '销售日期', '认购日期', '开始日期', '日期']))

      // 4. 备注：证券名称 + 委托状态
      const secName = getCellValue(row, ['证券名称', '产品名称'])
      const status = getCellValue(row, ['委托状态', '状态'])
      const remark = [secName, status].filter(Boolean).join(' | ')

      // 5. 过滤条件：销售人员为空或金额为0的跳过
      if (!salesPerson || amount <= 0) {
        skippedRows++
        return null
      }

      validRows++

      // 根据销售人员查找所属营业部
      const member = existingMembers.value.find(m => m.name === salesPerson)
      const groupName = member ? (groups.value.find(g => g.id === member.group_id)?.name || '未知营业部') : '未匹配'

      return {
        '销售人员': salesPerson,
        '所属营业部': groupName, // 自动匹配到的营业部
        '销售金额': amount.toFixed(2),
        '交易日期': saleDate,
        '备注': remark,
        '_raw': row // 保留原始数据用于调试
      }
    }).filter(Boolean)

    rowFilterStats.value = { total: totalRows, valid: validRows, skipped: skippedRows }
    previewData.value = mappedData

    nextStep()
  } catch (error) {
    console.error('[DEBUG] Upload error:', error)
    console.error('[DEBUG] Error response:', error.response)
    console.error('[DEBUG] Error data:', error.response?.data)
    const detail = error.response?.data?.detail || error.message || '上传失败'
    console.error('[DEBUG] Error detail:', JSON.stringify(detail, null, 2))
    ElMessage.error(`上传失败: ${JSON.stringify(detail)}`)
  } finally {
    uploading.value = false
  }
}

async function loadPreviewData() {
  nextStep()
}

async function executeImport() {
  importing.value = true
  try {
    // 将预览数据转换为后端需要的格式
    const records = previewData.value.map(row => ({
      member_name: String(row['销售人员'] || ''),
      group_name: String(row['所属营业部'] || ''),
      amount: String(row['销售金额'] || ''),
      sale_date: String(row['交易日期'] || ''),
      remark: String(row['备注'] || '')
    }))

    console.log('[DEBUG] Executing import:', { product_id: selectedProduct.value, records_count: records.length })

    const res = await importApi.execute({
      product_id: selectedProduct.value,
      records: records
    })

    if (res.failed > 0) {
      ElMessage.warning(`导入完成：成功${res.success}条，失败${res.failed}条`)
      importResult.value = res
    } else {
      ElMessage.success(`导入成功！成功${res.success}条`)
      nextStep()
    }
  } catch (error) {
    console.error('[DEBUG] Import error:', error)
    console.error('[DEBUG] Error response:', error.response)
    const detail = error.response?.data?.detail || error.message || '导入失败'
    ElMessage.error(`导入失败: ${JSON.stringify(detail)}`)
  } finally {
    importing.value = false
  }
}

function resetWizard() {
  currentStep.value = 0
  selectedProduct.value = null
  uploadFileRaw.value = null
  previewData.value = []
  codeValidationResult.value = null
  rowFilterStats.value = { total: 0, valid: 0, skipped: 0 }
  importResult.value = null
}

function nextStep() {
  if (currentStep.value < 4) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

function downloadTemplate() {
  const templateData = [
    ['销售人员', '所属营业部', '销售金额', '交易日期', '备注'],
    ['张三', '北京营业部', '100000', '2024-01-15', ''],
    ['李四', '上海营业部', '500000', '2024-01-16', '大单'],
    ['王五', '深圳营业部', '200000', '2024-01-17', '']
  ]

  let csvContent = '\uFEFF'
  templateData.forEach(row => {
    csvContent += row.join(',') + '\n'
  })

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', '销售数据导入模板.csv')
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  ElMessage.success('模板下载成功')
}
</script>

<style scoped>
.import-page {
  max-width: 900px;
  margin: 0 auto;
}

/* 5步向导 */
.import-wizard {
  max-width: 900px;
  margin: 0 auto;
}

.wizard-steps {
  display: flex;
  justify-content: space-between;
  margin-bottom: 40px;
  position: relative;
}

.wizard-steps::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 60px;
  right: 60px;
  height: 2px;
  background: #E5E5EA;
  z-index: 0;
}

.wizard-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  z-index: 1;
}

.step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #E5E5EA;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #6E6E73;
  transition: all 0.3s ease;
}

.wizard-step.active .step-number,
.wizard-step.completed .step-number {
  background: #007AFF;
  color: white;
}

.wizard-step.completed .step-number {
  background: #34C759;
}

.step-label {
  font-size: 13px;
  color: #6E6E73;
  font-weight: 500;
}

.wizard-step.active .step-label {
  color: #007AFF;
  font-weight: 600;
}

.wizard-content {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  padding: 32px;
}

.wizard-step-content {
  display: none;
}

.wizard-step-content.active {
  display: block;
}

.step-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #1D1D1F;
}

.step-desc {
  color: #6E6E73;
  margin-bottom: 28px;
}

.selected-product-info {
  background: #F5F5F7;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 24px;
  border-left: 4px solid #007AFF;
}

.selected-product-label {
  font-size: 12px;
  color: #6E6E73;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.selected-product-name {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 4px;
}

.selected-product-code {
  font-size: 13px;
  color: #007AFF;
  font-weight: 500;
}

.product-select-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.product-select-item {
  padding: 16px;
  border: 2px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.product-select-item:hover {
  border-color: #007AFF;
}

.product-select-item.selected {
  border-color: #007AFF;
  background: rgba(0, 122, 255, 0.05);
}

.upload-area {
  border: 2px dashed rgba(0, 0, 0, 0.15);
  border-radius: 16px;
  padding: 60px;
  text-align: center;
  transition: all 0.2s ease;
  cursor: pointer;
}

.upload-area:hover {
  border-color: #007AFF;
  background: rgba(0, 122, 255, 0.02);
}

.upload-text {
  font-size: 16px;
  color: #1D1D1F;
  margin-bottom: 8px;
  font-weight: 500;
}

.upload-hint {
  font-size: 13px;
  color: #6E6E73;
}

.template-download {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  padding: 12px;
  background: #F5F5F7;
  border-radius: 8px;
}

.template-tip {
  font-size: 12px;
  color: #8E8E93;
}

.wizard-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.validation-result {
  background: #E3F5E8;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.validation-title {
  font-weight: 600;
  color: #059669;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.validation-list {
  list-style: none;
  font-size: 13px;
  color: #6E6E73;
  padding: 0;
  margin: 0;
}

.validation-list li {
  padding: 4px 0;
  padding-left: 20px;
  position: relative;
}

.validation-list li::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #34C759;
  font-weight: 700;
}

.preview-table-container {
  max-height: 400px;
  overflow: auto;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
  margin-bottom: 24px;
}

.success-check {
  text-align: center;
  padding: 40px;
}

.success-icon {
  width: 80px;
  height: 80px;
  background: #34C759;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  color: white;
  font-size: 40px;
  font-weight: 700;
}

.success-title {
  font-size: 24px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 8px;
}

.success-desc {
  color: #6E6E73;
  margin-bottom: 24px;
}

/* 汇总统计 */
.summary-stats-bar {
  display: flex;
  align-items: center;
  gap: 0;
  background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
  border-radius: 12px;
  padding: 20px 0;
  margin-bottom: 24px;
}

.summary-stat-item {
  flex: 1;
  text-align: center;
  padding: 0 16px;
}

.summary-stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 6px;
}

.summary-stat-value {
  font-size: 28px;
  font-weight: 700;
  color: white;
}

.summary-unit {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  margin-left: 2px;
}

.summary-stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
}
</style>
