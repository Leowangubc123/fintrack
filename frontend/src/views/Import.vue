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
          <div class="wizard-actions">
            <el-button @click="prevStep">上一步</el-button>
            <el-button type="primary" @click="loadPreviewData">下一步</el-button>
          </div>
        </div>

        <!-- 步骤4: 数据预览 -->
        <div v-if="currentStep === 3" class="wizard-step-content active">
          <div class="step-title">数据预览</div>
          <div class="step-desc">共 {{ previewData.length }} 条数据，请检查是否正确</div>
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
          <div class="success-check">
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
import { Upload, Check, Download } from '@element-plus/icons-vue'

const currentStep = ref(0)
const selectedProduct = ref(null)
const products = ref([])

// 获取选中的产品信息
const selectedProductInfo = computed(() => {
  return products.value.find(p => p.id === selectedProduct.value)
})
const uploadFileRaw = ref(null)
const uploading = ref(false)
const importing = ref(false)
const previewData = ref([])

const steps = ['选择产品', '上传文件', '字段映射', '数据预览', '完成']

const columnMapping = ref([
  { systemField: '销售人员', excelColumn: '销售人员', matched: true },
  { systemField: '所属营业部', excelColumn: '所属营业部', matched: true },
  { systemField: '销售金额', excelColumn: '销售金额', matched: true },
  { systemField: '交易日期', excelColumn: '交易日期', matched: true },
  { systemField: '备注', excelColumn: '备注', matched: true },
])

onMounted(() => {
  loadProducts()
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

function handleFileChange(file) {
  uploadFileRaw.value = file.raw
}

async function uploadFile() {
  if (!uploadFileRaw.value) return
  uploading.value = true
  try {
    console.log('[DEBUG] Uploading file:', uploadFileRaw.value.name, 'size:', uploadFileRaw.value.size)
    console.log('[DEBUG] Selected product:', selectedProduct.value)
    const res = await importApi.preview(selectedProduct.value, uploadFileRaw.value)
    const mapping = res.suggested_mapping || {}
    const rawPreview = res.preview || []

    // 将原始数据映射到系统字段
    previewData.value = rawPreview.map(row => {
      const mappedRow = {}
      // 使用中文列名直接映射
      if (mapping.member_name && row[mapping.member_name] !== undefined) {
        mappedRow['销售人员'] = row[mapping.member_name]
      }
      if (mapping.group_name && row[mapping.group_name] !== undefined) {
        mappedRow['所属营业部'] = row[mapping.group_name]
      }
      if (mapping.amount !== undefined && row[mapping.amount] !== undefined) {
        mappedRow['销售金额'] = row[mapping.amount]
      }
      if (mapping.sale_date && row[mapping.sale_date] !== undefined) {
        mappedRow['交易日期'] = row[mapping.sale_date]
      }
      if (mapping.remark && row[mapping.remark] !== undefined) {
        mappedRow['备注'] = row[mapping.remark]
      }

      // 如果没有匹配到映射，尝试直接匹配列名
      if (!mappedRow['销售人员'] && row['销售人员'] !== undefined) {
        mappedRow['销售人员'] = row['销售人员']
      }
      if (!mappedRow['所属营业部'] && row['所属营业部'] !== undefined) {
        mappedRow['所属营业部'] = row['所属营业部']
      }
      if (mappedRow['销售金额'] === undefined && row['销售金额'] !== undefined) {
        mappedRow['销售金额'] = row['销售金额']
      }
      if (!mappedRow['交易日期'] && row['交易日期'] !== undefined) {
        mappedRow['交易日期'] = row['交易日期']
      }
      if (!mappedRow['备注'] && row['备注'] !== undefined) {
        mappedRow['备注'] = row['备注']
      }

      return mappedRow
    })

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
    ElMessage.success(`导入成功！成功${res.success}条，失败${res.failed}条`)
    nextStep()
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
</style>
