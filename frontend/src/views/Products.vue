<template>
  <div class="products-page">
    <div class="card">
      <div class="card-body">
        <!-- 筛选Tabs with 新建产品按钮 -->
        <div class="header-section">
          <div class="tabs">
            <button
              v-for="tab in tabs"
              :key="tab.value"
              class="tab-btn"
              :class="{ active: filterStatus === tab.value }"
              @click="filterStatus = tab.value; loadProducts()"
            >
              {{ tab.label }}
            </button>
          </div>
          <button class="btn btn-primary" @click="showDialog = true">
            <span class="btn-icon">+</span>
            新建产品
          </button>
        </div>

        <!-- 在售产品网格 -->
        <div class="product-grid" v-loading="loading">
          <div
            v-for="product in activeProducts"
            :key="product.id"
            class="product-card"
          >
            <div class="product-card-header">
              <span class="status-dot" :class="getStatusDotClass(product.status)"></span>
              <span class="product-name">{{ product.name }}</span>
              <span class="tag" :class="getStatusTagClass(product.status)">
                {{ product.status }}
              </span>
            </div>
            <div class="product-card-body">
              <div class="info-row">
                <span class="info-label">类型:</span>
                <span class="info-value">{{ product.type }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">发行:</span>
                <span class="info-value">{{ product.issuer }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">募集期:</span>
                <span class="info-value">{{ formatDate(product.start_date) }} - {{ formatDate(product.end_date) }}</span>
              </div>
              <div class="product-progress-box">
                <div class="progress-header">
                  <span class="progress-target">目标: ¥{{ formatNumber(product.total_target) }}万</span>
                  <span class="progress-percentage" :class="getProgressColorClass(product)">
                    {{ calculateProgress(product) }}%
                  </span>
                </div>
                <div class="progress-bar">
                  <div
                    class="progress-segment"
                    :class="getProgressBarClass(product)"
                    :style="{ width: calculateProgress(product) + '%' }"
                  ></div>
                </div>
                <div class="progress-footer">
                  任务分配: <span class="progress-assigned">{{ getAssignedCount(product) }}/{{ getTotalAssignees(product) }}</span> 人
                </div>
              </div>
              <div class="card-actions">
                <button class="btn-link" @click="handleEdit(product)">编辑</button>
                <button class="btn-link" @click="handleData(product)">数据</button>
                <button
                  class="btn-link btn-danger"
                  :class="{ disabled: !canArchive(product) }"
                  @click="handleArchive(product)"
                >
                  {{ product.status === '已归档' ? '删除' : '归档' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <el-empty v-if="activeProducts.length === 0 && !loading" description="暂无产品" />

        <!-- 已归档产品 -->
        <div v-if="archivedProducts.length > 0" class="archived-section">
          <div class="archived-header">
            <span class="archived-title">
              <span class="archived-icon">📁</span>
              已归档产品
            </span>
            <button class="btn btn-secondary" @click="showArchived = !showArchived">
              {{ showArchived ? '收起' : '展开' }}
            </button>
          </div>
          <div v-show="showArchived" class="archived-grid">
            <div
              v-for="product in archivedProducts"
              :key="product.id"
              class="archived-card"
            >
              <div class="archived-header-row">
                <span class="archived-product-name">{{ product.name }}</span>
                <span class="archived-tag">已归档</span>
              </div>
              <div class="archived-date">
                <span class="archived-date-label">归档日期</span>
                {{ formatDate(product.archived_at || product.end_date) }}
              </div>
              <div class="archived-stats">
                <div class="archived-stat">
                  <div class="archived-stat-value">¥{{ formatNumber(product.actual_amount || 0) }}万</div>
                  <div class="archived-stat-label">实际募集</div>
                </div>
                <div class="archived-stat">
                  <div class="archived-stat-value" :style="{ color: getCompletionRateColor(product) }">
                    {{ calculateCompletionRate(product) }}%
                  </div>
                  <div class="archived-stat-label">完成率</div>
                </div>
              </div>
              <div class="archived-actions">
                <button class="btn-link" @click="handleEdit(product)">编辑</button>
                <button class="btn-link btn-danger" @click="handleDelete(product)">删除</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建产品弹窗 -->
    <el-dialog
      v-model="showDialog"
      title="新建产品"
      width="600px"
      :close-on-click-modal="false"
      class="apple-dialog"
      destroy-on-close
    >
      <el-form
        :model="form"
        :rules="rules"
        ref="formRef"
        label-position="top"
        class="apple-form"
      >
        <!-- 基本信息 -->
        <div class="form-section">
          <div class="form-section-title">基本信息</div>
          <el-form-item label="产品名称" prop="name">
            <el-input
              v-model="form.name"
              placeholder="请输入产品正式名称"
              class="apple-input"
            />
          </el-form-item>
          <div class="form-row">
            <el-form-item label="产品类型" prop="type" class="form-col">
              <el-select
                v-model="form.type"
                placeholder="请选择产品类型"
                class="apple-select"
                style="width: 100%"
              >
                <el-option label="公募产品" value="公募产品" />
                <el-option label="私募产品" value="私募产品" />
                <el-option label="资管产品" value="资管产品" />
                <el-option label="其他产品" value="其他产品" />
              </el-select>
            </el-form-item>
            <el-form-item label="产品代码" prop="code" class="form-col">
              <el-input
                v-model="form.code"
                placeholder="请输入官方产品代码"
                class="apple-input"
              />
            </el-form-item>
          </div>
          <el-form-item label="发行机构" prop="issuer">
            <el-input
              v-model="form.issuer"
              placeholder="请输入产品发行方名称"
              class="apple-input"
            />
          </el-form-item>
        </div>

        <!-- 募集信息 -->
        <div class="form-section">
          <div class="form-section-title">募集信息</div>
          <el-form-item label="全公司总目标额" prop="total_target">
            <el-input-number
              v-model="form.total_target"
              :min="0"
              :precision="2"
              placeholder="请输入总目标金额"
              class="apple-input-number"
              style="width: 100%"
              controls-position="right"
            >
              <template #suffix>
                <span class="input-unit">万元</span>
              </template>
            </el-input-number>
          </el-form-item>
          <div class="form-row">
            <el-form-item label="募集开始日期" prop="start_date" class="form-col">
              <el-date-picker
                v-model="form.start_date"
                type="date"
                placeholder="选择开始日期"
                class="apple-date-picker"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item label="募集结束日期" prop="end_date" class="form-col">
              <el-date-picker
                v-model="form.end_date"
                type="date"
                placeholder="选择结束日期"
                class="apple-date-picker"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </div>
        </div>

        <!-- 产品说明 -->
        <div class="form-section">
          <div class="form-section-title">产品说明</div>
          <el-form-item label="产品说明/备注">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="3"
              placeholder="请输入产品说明、投资策略等详细信息（选填）"
              class="apple-textarea"
              resize="none"
            />
          </el-form-item>
        </div>

        <!-- 提示信息 -->
        <div class="info-tip">
          <span class="tip-icon">💡</span>
          <span>产品创建成功后，可在产品列表中进行营业部及个人的任务分配</span>
        </div>
      </el-form>
      <template #footer>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDialog = false">取消</button>
          <button class="btn btn-primary" :disabled="submitting" @click="submitForm">
            <span v-if="submitting" class="loading-spinner"></span>
            {{ submitting ? '创建中...' : '创建产品' }}
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑产品弹窗 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑产品"
      width="600px"
      :close-on-click-modal="false"
      class="apple-dialog"
      destroy-on-close
    >
      <el-form
        :model="editForm"
        :rules="rules"
        ref="editFormRef"
        label-position="top"
        class="apple-form"
      >
        <!-- 基本信息 -->
        <div class="form-section">
          <div class="form-section-title">基本信息</div>
          <el-form-item label="产品名称" prop="name">
            <el-input v-model="editForm.name" placeholder="请输入产品正式名称" class="apple-input" />
          </el-form-item>
          <div class="form-row">
            <el-form-item label="产品类型" prop="type" class="form-col">
              <el-select v-model="editForm.type" style="width: 100%" class="apple-select">
                <el-option label="公募产品" value="公募产品" />
                <el-option label="私募产品" value="私募产品" />
                <el-option label="资管产品" value="资管产品" />
                <el-option label="其他产品" value="其他产品" />
              </el-select>
            </el-form-item>
            <el-form-item label="产品代码" prop="code" class="form-col">
              <el-input v-model="editForm.code" placeholder="请输入官方产品代码" class="apple-input" />
            </el-form-item>
          </div>
          <el-form-item label="发行机构" prop="issuer">
            <el-input v-model="editForm.issuer" placeholder="请输入产品发行方名称" class="apple-input" />
          </el-form-item>
        </div>

        <!-- 募集信息 -->
        <div class="form-section">
          <div class="form-section-title">募集信息</div>
          <el-form-item label="全公司总目标额" prop="total_target">
            <el-input-number
              v-model="editForm.total_target"
              :min="0"
              :precision="2"
              style="width: 100%"
              class="apple-input-number"
              controls-position="right"
            />
          </el-form-item>
          <div class="form-row">
            <el-form-item label="募集开始日期" prop="start_date" class="form-col">
              <el-date-picker
                v-model="editForm.start_date"
                type="date"
                style="width: 100%"
                class="apple-date-picker"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item label="募集结束日期" prop="end_date" class="form-col">
              <el-date-picker
                v-model="editForm.end_date"
                type="date"
                style="width: 100%"
                class="apple-date-picker"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </div>
        </div>

        <!-- 产品说明 -->
        <div class="form-section">
          <div class="form-section-title">产品说明</div>
          <el-form-item label="产品说明/备注">
            <el-input
              v-model="editForm.description"
              type="textarea"
              :rows="3"
              class="apple-textarea"
              resize="none"
            />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showEditDialog = false">取消</button>
          <button class="btn btn-primary" :disabled="updating" @click="submitEdit">
            <span v-if="updating" class="loading-spinner"></span>
            {{ updating ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { productsApi } from '../api'

const products = ref([])
const loading = ref(false)
const submitting = ref(false)
const updating = ref(false)
const showDialog = ref(false)
const showEditDialog = ref(false)
const showArchived = ref(true)
const filterStatus = ref('')
const formRef = ref(null)
const editFormRef = ref(null)

const tabs = [
  { label: '全部', value: '' },
  { label: '募集中', value: '募集中' },
  { label: '待开始', value: '待开始' },
  { label: '已结束', value: '已结束' },
  { label: '已归档', value: '已归档' }
]

const form = ref({
  name: '',
  type: '',
  issuer: '',
  code: '',
  start_date: null,
  end_date: null,
  total_target: 0,
  description: ''
})

const editForm = ref({
  id: null,
  name: '',
  type: '',
  issuer: '',
  code: '',
  start_date: null,
  end_date: null,
  total_target: 0,
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入产品名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择产品类型', trigger: 'change' }],
  issuer: [{ required: true, message: '请输入发行机构', trigger: 'blur' }],
  code: [{ required: true, message: '请输入产品代码', trigger: 'blur' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
  total_target: [{ required: true, message: '请输入目标金额', trigger: 'blur' }]
}

const activeProducts = computed(() => {
  return products.value.filter(p => p.status !== '已归档')
})

const archivedProducts = computed(() => {
  return products.value.filter(p => p.status === '已归档')
})

onMounted(() => {
  loadProducts()
})

async function loadProducts() {
  loading.value = true
  try {
    const res = await productsApi.list({ status: filterStatus.value })
    products.value = res
  } catch (error) {
    ElMessage.error('加载产品失败')
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await productsApi.create(form.value)
    ElMessage.success('产品创建成功')
    showDialog.value = false
    resetForm()
    loadProducts()
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  form.value = {
    name: '',
    type: '',
    issuer: '',
    code: '',
    start_date: null,
    end_date: null,
    total_target: 0,
    description: ''
  }
  formRef.value?.resetFields()
}

function handleEdit(product) {
  editForm.value = { ...product }
  showEditDialog.value = true
}

async function submitEdit() {
  const valid = await editFormRef.value.validate().catch(() => false)
  if (!valid) return

  updating.value = true
  try {
    await productsApi.update(editForm.value.id, editForm.value)
    ElMessage.success('产品更新成功')
    showEditDialog.value = false
    loadProducts()
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    updating.value = false
  }
}

function handleData(product) {
  // Navigate to product detail/data page
  ElMessage.info(`查看产品数据: ${product.name}`)
}

async function handleArchive(product) {
  try {
    await ElMessageBox.confirm(
      `确定要归档产品 "${product.name}" 吗？`,
      '确认归档',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await productsApi.archive(product.id)
    ElMessage.success('产品已归档')
    loadProducts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('归档失败')
    }
  }
}

async function handleDelete(product) {
  try {
    await ElMessageBox.confirm(
      `确定要删除产品 "${product.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'danger'
      }
    )
    await productsApi.delete(product.id)
    ElMessage.success('产品已删除')
    loadProducts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function getStatusDotClass(status) {
  const classes = {
    '募集中': 'dot-active',
    '待开始': 'dot-pending',
    '已结束': 'dot-ended',
    '已归档': 'dot-ended'
  }
  return classes[status] || 'dot-ended'
}

function getStatusTagClass(status) {
  const classes = {
    '募集中': 'tag-primary',
    '待开始': 'tag-warning',
    '已结束': 'tag-info',
    '已归档': 'tag-archive'
  }
  return classes[status] || 'tag-info'
}

function calculateProgress(product) {
  if (!product.total_target || product.total_target === 0) return 0
  const raised = product.raised_amount || product.current_amount || 0
  return Math.min(Math.round((raised / product.total_target) * 100), 100)
}

function getProgressColorClass(product) {
  const progress = calculateProgress(product)
  if (progress >= 80) return 'text-green'
  if (progress >= 50) return 'text-yellow'
  if (progress >= 20) return 'text-orange'
  return 'text-gray'
}

function getProgressBarClass(product) {
  const progress = calculateProgress(product)
  if (progress >= 80) return 'progress-green'
  if (progress >= 50) return 'progress-yellow'
  if (progress >= 20) return 'progress-orange'
  return 'progress-gray'
}

function getAssignedCount(product) {
  return product.assigned_count || 0
}

function getTotalAssignees(product) {
  return product.total_assignees || 20
}

function canArchive(product) {
  return product.status === '已结束' || product.status === '募集中'
}

function calculateCompletionRate(product) {
  if (!product.total_target || product.total_target === 0) return 0
  const actual = product.actual_amount || product.raised_amount || 0
  return Math.round((actual / product.total_target) * 100)
}

function getCompletionRateColor(product) {
  const rate = calculateCompletionRate(product)
  if (rate >= 100) return '#34C759'
  if (rate >= 80) return '#FFCC00'
  if (rate >= 60) return '#FF9500'
  return '#FF3B30'
}

function formatNumber(num) {
  if (!num) return '0'
  return Number(num).toLocaleString()
}

function formatDate(date) {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
/* Apple Design System Colors */
:root {
  --apple-blue: #007AFF;
  --apple-blue-hover: #0056CC;
  --apple-green: #34C759;
  --apple-orange: #FF9500;
  --apple-yellow: #FFCC00;
  --apple-red: #FF3B30;
  --apple-text: #1D1D1F;
  --apple-text-secondary: #6E6E73;
  --apple-background: #F5F5F7;
  --apple-border: rgba(0, 0, 0, 0.08);
}

.products-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 32px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', sans-serif;
}

/* Card Styles */
.card {
  background: #FFFFFF;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.card-body {
  padding: 24px;
}

/* Header Section */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: #F5F5F7;
  border-radius: 10px;
  width: fit-content;
}

.tab-btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  background: transparent;
  color: #6E6E73;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: #007AFF;
}

.tab-btn.active {
  background: #FFFFFF;
  color: #007AFF;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* Buttons */
.btn {
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-primary {
  background: #007AFF;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056CC;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #F5F5F7;
  color: #1D1D1F;
}

.btn-secondary:hover {
  background: #E8E8ED;
}

.btn-icon {
  font-size: 16px;
  font-weight: 400;
}

/* Product Grid */
.product-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

@media (max-width: 1200px) {
  .product-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .product-grid {
    grid-template-columns: 1fr;
  }
}

/* Product Card */
.product-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
}

.product-card-header {
  padding: 18px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-active { background: #34C759; }
.dot-pending { background: #FFCC00; }
.dot-ended { background: #8E8E93; }

.product-name {
  flex: 1;
  font-weight: 600;
  color: #1D1D1F;
  font-size: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.tag-primary {
  background: #E8F4FF;
  color: #007AFF;
}

.tag-warning {
  background: #FFF4E0;
  color: #FF9500;
}

.tag-info {
  background: #F5F5F7;
  color: #6E6E73;
}

.tag-archive {
  background: #E5E5EA;
  color: #6E6E73;
}

.product-card-body {
  padding: 20px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 13px;
}

.info-label {
  color: #6E6E73;
}

.info-value {
  color: #1D1D1F;
  font-weight: 500;
}

/* Progress Box */
.product-progress-box {
  background: #F5F5F7;
  border-radius: 10px;
  padding: 14px;
  margin-top: 14px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 8px;
}

.progress-target {
  color: #6E6E73;
}

.progress-percentage {
  font-weight: 600;
}

.text-green { color: #34C759; }
.text-yellow { color: #FFCC00; }
.text-orange { color: #FF9500; }
.text-gray { color: #8E8E93; }

.progress-bar {
  height: 8px;
  background: #E5E5EA;
  border-radius: 4px;
  overflow: hidden;
}

.progress-segment {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-green { background: #34C759; }
.progress-yellow { background: #FFCC00; }
.progress-orange { background: #FF9500; }
.progress-gray { background: #8E8E93; }

.progress-footer {
  margin-top: 8px;
  font-size: 12px;
  color: #6E6E73;
}

.progress-assigned {
  color: #007AFF;
  font-weight: 600;
}

/* Card Actions */
.card-actions {
  display: flex;
  justify-content: space-around;
  padding: 14px 0 0;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  margin-top: 16px;
}

.btn-link {
  color: #007AFF;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 6px;
  transition: background 0.2s ease;
  border: none;
  background: transparent;
}

.btn-link:hover:not(.disabled) {
  background: rgba(0, 122, 255, 0.1);
}

.btn-link.btn-danger {
  color: #FF3B30;
}

.btn-link.btn-danger:hover:not(.disabled) {
  background: rgba(255, 59, 48, 0.1);
}

.btn-link.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Archived Section */
.archived-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.archived-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.archived-title {
  font-size: 17px;
  font-weight: 600;
  color: #1D1D1F;
  display: flex;
  align-items: center;
  gap: 8px;
}

.archived-icon {
  font-size: 18px;
}

.archived-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

@media (max-width: 1200px) {
  .archived-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .archived-grid {
    grid-template-columns: 1fr;
  }
}

.archived-card {
  background: white;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  padding: 20px;
  opacity: 0.85;
  transition: all 0.2s ease;
}

.archived-card:hover {
  opacity: 1;
  border-color: rgba(0, 0, 0, 0.15);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

.archived-header-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.archived-product-name {
  font-weight: 600;
  color: #1D1D1F;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.archived-tag {
  padding: 4px 10px;
  background: #E5E5EA;
  color: #6E6E73;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}

.archived-date {
  font-size: 13px;
  color: #1D1D1F;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #F5F5F7;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.archived-date-label {
  font-size: 11px;
  font-weight: 600;
  color: #6E6E73;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 2px 8px;
  background: #E5E5EA;
  border-radius: 4px;
}

.archived-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.archived-stat {
  text-align: center;
  padding: 12px;
  background: #F5F5F7;
  border-radius: 8px;
}

.archived-stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1D1D1F;
  margin-bottom: 4px;
}

.archived-stat-label {
  font-size: 12px;
  color: #6E6E73;
}

.archived-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

/* Modal Styles */
:deep(.apple-dialog) {
  border-radius: 20px;
  overflow: hidden;
}

:deep(.apple-dialog .el-dialog__header) {
  padding: 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  margin-right: 0;
}

:deep(.apple-dialog .el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #1D1D1F;
}

:deep(.apple-dialog .el-dialog__body) {
  padding: 20px 24px;
  max-height: 60vh;
  overflow-y: auto;
}

:deep(.apple-dialog .el-dialog__footer) {
  padding: 0;
  border-top: none;
}

.modal-footer {
  padding: 20px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* Form Styles */
.apple-form :deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 600;
  color: #1D1D1F;
  padding-bottom: 8px;
  line-height: 1.4;
}

.apple-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.apple-form :deep(.el-form-item.is-required .el-form-item__label::before) {
  color: #FF3B30;
  margin-right: 2px;
}

.form-section {
  margin-bottom: 24px;
}

.form-section:last-of-type {
  margin-bottom: 0;
}

.form-section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-col {
  flex: 1;
}

/* Input Styles */
.apple-input :deep(.el-input__wrapper),
.apple-select :deep(.el-input__wrapper),
.apple-date-picker :deep(.el-input__wrapper),
.apple-input-number :deep(.el-input__wrapper) {
  padding: 10px 14px;
  border-radius: 10px;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1) inset;
  transition: all 0.2s ease;
}

.apple-input :deep(.el-input__wrapper:hover),
.apple-select :deep(.el-input__wrapper:hover),
.apple-date-picker :deep(.el-input__wrapper:hover),
.apple-input-number :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.15) inset;
}

.apple-input :deep(.el-input__wrapper.is-focus),
.apple-select :deep(.el-input__wrapper.is-focus),
.apple-date-picker :deep(.el-input__wrapper.is-focus),
.apple-input-number :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #007AFF inset;
}

.apple-input :deep(.el-input__inner),
.apple-select :deep(.el-input__inner),
.apple-date-picker :deep(.el-input__inner),
.apple-input-number :deep(.el-input__inner) {
  font-size: 14px;
  color: #1D1D1F;
}

.apple-input-number :deep(.el-input-number__decrease),
.apple-input-number :deep(.el-input-number__increase) {
  border-radius: 0 10px 10px 0;
  border-left: 1px solid rgba(0, 0, 0, 0.08);
  background: #F5F5F7;
}

.apple-textarea :deep(.el-textarea__inner) {
  padding: 10px 14px;
  border-radius: 10px;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1) inset;
  border: none;
  font-size: 14px;
  color: #1D1D1F;
  resize: none;
  transition: all 0.2s ease;
}

.apple-textarea :deep(.el-textarea__inner:hover) {
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.15) inset;
}

.apple-textarea :deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 1px #007AFF inset;
}

.input-unit {
  color: #6E6E73;
  font-size: 13px;
  margin-left: 4px;
}

/* Info Tip */
.info-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #F5F5F7;
  border-radius: 10px;
  font-size: 13px;
  color: #6E6E73;
  margin-top: 20px;
}

.tip-icon {
  font-size: 14px;
}

/* Loading Spinner */
.loading-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 6px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty State */
:deep(.el-empty) {
  padding: 60px 0;
}

:deep(.el-empty__description) {
  color: #6E6E73;
  font-size: 14px;
  margin-top: 16px;
}
</style>
