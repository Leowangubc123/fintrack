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
          <div class="preview-table-container">
            <el-table :data="previewData" height="350">
              <el-table-column type="index" label="序号" width="60" />
              <el-table-column prop="member_name" label="成员姓名" />
              <el-table-column prop="group_name" label="营业部" />
              <el-table-column prop="amount" label="销售金额" />
              <el-table-column prop="sale_date" label="日期" />
            </el-table>
          </div>
          <div class="wizard-actions">
            <el-button @click="prevStep">上一步</el-button>
            <el-button type="primary" @click="nextStep">下一步</el-button>
          </div>
        </div>

        <!-- 步骤5: 完成导入 -->
        <div v-if="currentStep === 4" class="wizard-step-content active">
          <div class="success-check">
            <div class="success-icon">✓</div>
            <div class="success-title">导入成功！</div>
            <div class="success-desc">
              成功导入 {{ previewData.length }} 条销售记录
            </div>
            <el-button type="primary" @click="resetWizard">完成</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { productsApi, importApi } from '../api'
import { Upload, Check } from '@element-plus/icons-vue'

const currentStep = ref(0)
const selectedProduct = ref(null)
const products = ref([])
const uploadFileRaw = ref(null)
const uploading = ref(false)
const importing = ref(false)
const previewData = ref([])

const steps = ['选择产品', '上传文件', '字段映射', '数据预览', '完成']

const columnMapping = ref([
  { systemField: '成员姓名', excelColumn: '销售人员', matched: true },
  { systemField: '所属营业部', excelColumn: '所属团队', matched: true },
  { systemField: '销售金额', excelColumn: '认购金额', matched: true },
  { systemField: '销售日期', excelColumn: '交易日期', matched: true },
])

onMounted(() => {
  loadProducts()
})

async function loadProducts() {
  try {
    const res = await productsApi.list({ status: '募集中' })
    products.value = res
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
    const res = await importApi.preview(selectedProduct.value, uploadFileRaw.value)
    previewData.value = res.preview || []
    nextStep()
  } catch (error) {
    ElMessage.error('上传失败')
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
    await importApi.execute({
      product_id: selectedProduct.value,
      records: previewData.value
    })
    ElMessage.success('导入成功！')
    nextStep()
  } catch (error) {
    ElMessage.error('导入失败')
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
