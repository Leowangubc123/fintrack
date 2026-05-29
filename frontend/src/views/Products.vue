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

        <!-- 在售产品网格 - 只在非"已归档"标签页显示 -->
        <template v-if="filterStatus !== '已归档'">
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
                  <span class="info-label">代码:</span>
                  <span class="info-value" style="font-family: monospace; font-weight: 600;">{{ product.code || '—' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">募集期:</span>
                  <span class="info-value">{{ formatDate(product.start_date) }} - {{ formatDate(product.end_date) }}</span>
                </div>
                <div class="product-progress-box">
                  <div class="progress-stats-row">
                    <div class="progress-stat">
                      <span class="progress-stat-label">目标销量</span>
                      <span class="progress-stat-value">¥{{ formatNumber(product.total_target) }}万</span>
                    </div>
                    <div class="progress-stat">
                      <span class="progress-stat-label">累积销量</span>
                      <span class="progress-stat-value actual">¥{{ formatNumber(product.raised_amount || 0) }}万</span>
                    </div>
                    <span class="progress-percentage" :class="getProgressColorClass(product)">
                      {{ calculateProgress(product) }}%
                    </span>
                  </div>
                  <div class="progress-bar">
                    <div
                      class="progress-segment"
                      :class="getProgressBarClass(product)"
                      :style="{ width: Math.min(calculateProgress(product), 100) + '%' }"
                    ></div>
                  </div>
                  <div class="progress-footer">
                    <button class="btn-link btn-danger" @click="handleClearSalesData(product)">清空销售数据</button>
                  </div>
                </div>
                <div class="card-actions">
                  <button class="btn-link" @click="openAssignModal(product)">任务分配</button>
                  <button class="btn-link" @click="handleEdit(product)">编辑</button>
                  <button
                    class="btn-link btn-danger"
                    :class="{ disabled: !canArchive(product) }"
                    @click="handleArchive(product)"
                  >
                    归档
                  </button>
                  <button class="btn-link btn-danger" @click="handleDelete(product)">删除</button>
                </div>
              </div>
            </div>
          </div>

          <el-empty v-if="activeProducts.length === 0 && !loading" description="暂无产品" />
        </template>

        <!-- 已归档产品 - 只在"已归档"标签页显示 -->
        <div v-if="filterStatus === '已归档' && archivedProducts.length > 0" class="archived-section">
          <div class="archived-header">
            <div style="display: flex; align-items: center; gap: 16px;">
              <span class="archived-title">
                <span class="archived-icon">📁</span>
                已归档产品 ({{ archivedProducts.length }})
              </span>
              <el-select v-model="archivedYear" size="small" style="width: 100px;">
                <el-option
                  v-for="year in yearOptions"
                  :key="year"
                  :label="year + '年'"
                  :value="year"
                />
              </el-select>
            </div>
          </div>
          <div class="archived-grid">
            <div
              v-for="product in archivedProducts"
              :key="product.id"
              class="archived-card"
            >
              <div class="archived-header-row">
                <span class="archived-product-name">{{ product.name }}</span>
                <span class="archived-tag">已归档</span>
              </div>
              <div class="archived-meta">
                <span v-if="product.code" class="archived-code-tag">{{ product.code }}</span>
                <span class="archived-period">{{ formatDate(product.start_date) }} — {{ formatDate(product.end_date) }}</span>
              </div>
              <div class="archived-stats">
                <div class="archived-stat">
                  <div class="archived-stat-value">¥{{ formatNumber(product.raised_amount || 0) }}万</div>
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
                <button class="btn-link" style="color: #34C759;" @click="handleUnarchive(product)">解除归档</button>
                <button class="btn-link btn-danger" @click="handleDelete(product)">删除</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 已归档产品 - 空状态（也显示年份选择器） -->
        <div v-if="filterStatus === '已归档' && archivedProducts.length === 0 && !loading" class="archived-section">
          <div class="archived-header" style="margin-bottom: 0;">
            <div style="display: flex; align-items: center; gap: 16px;">
              <span class="archived-title">
                <span class="archived-icon">📁</span>
                已归档产品
              </span>
              <el-select v-model="archivedYear" size="small" style="width: 100px;">
                <el-option
                  v-for="year in yearOptions"
                  :key="year"
                  :label="year + '年'"
                  :value="year"
                />
              </el-select>
            </div>
          </div>
          <el-empty description="该年度暂无已归档产品" :image-size="80" style="padding: 20px 0;" />
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

    <!-- 任务分配弹窗 -->
    <el-dialog
      v-model="showAssignModal"
      :title="`任务分配 - ${assignProduct?.name || ''}`"
      width="800px"
      :close-on-click-modal="false"
      class="apple-dialog assign-dialog"
      destroy-on-close
    >
      <div class="assign-modal-body" v-if="assignProduct">
        <!-- 分配概览 -->
        <div class="assign-summary">
          <div class="assign-summary-item">
            <div class="assign-summary-label">产品总目标</div>
            <div class="assign-summary-value">¥{{ formatNumber(assignProduct.total_target) }}万</div>
          </div>
          <div class="assign-summary-item">
            <div class="assign-summary-label">已分配营业部</div>
            <div class="assign-summary-value" :style="{ color: '#34C759' }">¥{{ formatNumber(groupAssignedTotal) }}万</div>
          </div>
          <div class="assign-summary-item">
            <div class="assign-summary-label">未分配</div>
            <div class="assign-summary-value" :style="{ color: unassignedAmount > 0 ? '#FF9500' : '#34C759' }">¥{{ formatNumber(unassignedAmount) }}万</div>
          </div>
          <div class="assign-summary-item">
            <div class="assign-summary-label">分配进度</div>
            <div class="assign-summary-value">{{ assignProgress }}%</div>
          </div>
        </div>

        <!-- 标签切换 -->
        <div class="assign-tabs">
          <button
            class="assign-tab"
            :class="{ active: assignStep === 1 }"
            @click="assignStep = 1"
          >
            <span class="tab-number">1</span>
            <span>营业部任务分配</span>
          </button>
          <button
            class="assign-tab"
            :class="{ active: assignStep === 2 }"
            @click="assignStep = 2"
          >
            <span class="tab-number">2</span>
            <span>个人任务分配</span>
          </button>
        </div>

        <!-- 步骤1: 营业部任务分配 -->
        <div v-show="assignStep === 1" class="assign-step-content">
          <div class="assign-step-header">
            <span class="assign-step-title">营业部任务分配</span>
            <span class="assign-step-subtitle">共 {{ groups.length }} 个营业部</span>
          </div>
          <div class="assign-table-wrapper">
            <table class="assign-table">
              <thead>
                <tr>
                  <th>营业部</th>
                  <th style="text-align: center;">成员数</th>
                  <th style="text-align: right;">分配任务</th>
                  <th style="text-align: right;">人均任务</th>
                  <th style="text-align: center;">任务占比</th>
                  <th style="text-align: center;">状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="group in assignGroups" :key="group.id">
                  <td>
                    <div class="assign-group-name">{{ group.name }}</div>
                    <div class="assign-group-leader">{{ group.leader || '暂无负责人' }}</div>
                  </td>
                  <td style="text-align: center;">{{ group.member_count || 0 }}</td>
                  <td style="text-align: right;">
                    <el-input-number
                      v-model="group.target"
                      :min="0"
                      :precision="2"
                      :step="10"
                      size="small"
                      style="width: 120px"
                      controls-position="right"
                      @change="updateGroupTarget(group)"
                    />
                    <span class="input-unit">万</span>
                  </td>
                  <td style="text-align: right; font-weight: 500;">
                    {{ group.member_count ? formatNumber(Math.round(group.target / group.member_count)) : '-' }}
                  </td>
                  <td style="text-align: center;">{{ calculateGroupRatio(group.target) }}%</td>
                  <td style="text-align: center;">
                    <span
                      class="assign-status-tag"
                      :class="getAssignStatusClass(group.target)"
                    >
                      {{ group.target > 0 ? '已分配' : '待分配' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="assign-actions">
            <button class="btn btn-primary" @click="saveGroupAssign" :disabled="savingGroupAssign">
              {{ savingGroupAssign ? '保存中...' : '保存营业部分配' }}
            </button>
          </div>
        </div>

        <!-- 步骤2: 个人任务分配 -->
        <div v-show="assignStep === 2" class="assign-step-content">
          <div class="assign-step-header">
            <div>
              <span class="assign-step-title">个人任务分配</span>
              <span class="assign-step-subtitle" style="margin-left: 12px;">
                {{ selectedAssignGroup?.name || '' }} ({{ selectedGroupMembers.length }}人)
              </span>
            </div>
            <el-select
              v-model="selectedGroupId"
              placeholder="选择营业部"
              size="small"
              style="width: 160px"
              @change="onGroupChange"
            >
              <el-option
                v-for="group in assignGroups"
                :key="group.id"
                :label="group.name"
                :value="group.id"
              />
            </el-select>
          </div>

          <!-- 营业部分配概览 -->
          <div v-if="selectedAssignGroup" class="group-assign-overview">
            <div class="overview-item">
              <span class="overview-label">营业部总任务</span>
              <span class="overview-value">¥{{ formatNumber(selectedAssignGroup.target) }}万</span>
            </div>
            <div class="overview-divider"></div>
            <div class="overview-item">
              <span class="overview-label">已分配个人</span>
              <span class="overview-value" :style="{ color: '#34C759' }">¥{{ formatNumber(memberAssignedTotal) }}万</span>
            </div>
            <div class="overview-divider"></div>
            <div class="overview-item">
              <span class="overview-label">剩余未分配</span>
              <span class="overview-value" :style="{ color: memberUnassigned > 0 ? '#FF9500' : '#34C759' }">¥{{ formatNumber(memberUnassigned) }}万</span>
            </div>
          </div>

          <div class="assign-table-wrapper">
            <table class="assign-table">
              <thead>
                <tr>
                  <th style="width: 50px; text-align: center;">
                    <el-checkbox v-model="selectAllMembers" @change="toggleSelectAllMembers" />
                  </th>
                  <th>营销人员</th>
                  <th style="text-align: right;">分配任务</th>
                  <th style="text-align: center;">任务占比</th>
                  <th style="text-align: center;">状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="member in selectedGroupMembers" :key="member.id">
                  <td style="text-align: center;">
                    <el-checkbox v-model="member.selected" />
                  </td>
                  <td>
                    <div class="assign-member-info">
                      <div class="assign-member-name">{{ member.name }}</div>
                      <div class="assign-member-code">{{ member.code || '暂无工号' }}</div>
                    </div>
                  </td>
                  <td style="text-align: right;">
                    <el-input-number
                      v-model="member.target"
                      :min="0"
                      :precision="2"
                      :step="5"
                      size="small"
                      style="width: 110px"
                      controls-position="right"
                      @change="updateMemberTarget(member)"
                      :disabled="!member.selected"
                    />
                    <span class="input-unit">万</span>
                  </td>
                  <td style="text-align: center;">{{ calculateMemberRatio(member.target) }}%</td>
                  <td style="text-align: center;">
                    <span
                      class="assign-status-tag"
                      :class="getAssignStatusClass(member.selected ? member.target : 0)"
                    >
                      {{ member.selected && member.target > 0 ? '已分配' : '待分配' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="assign-actions">
            <button class="btn btn-secondary" @click="autoDistributeToMembers">自动均分</button>
            <button class="btn btn-primary" @click="saveMemberAssign" :disabled="savingMemberAssign">
              {{ savingMemberAssign ? '保存中...' : '保存个人分配' }}
            </button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { productsApi, groupsApi, membersApi } from '../api'

const products = ref([])
const loading = ref(false)
const submitting = ref(false)
const updating = ref(false)
const showDialog = ref(false)
const showEditDialog = ref(false)
const filterStatus = ref('')
const archivedYear = ref(new Date().getFullYear()) // 默认显示本年度
const formRef = ref(null)
const editFormRef = ref(null)

// 任务分配相关
const showAssignModal = ref(false)
const assignProduct = ref(null)
const assignStep = ref(1)
const groups = ref([])
const assignGroups = ref([])
const selectedGroupId = ref(null)
const selectedGroupMembers = ref([])
const selectAllMembers = ref(false)
const savingGroupAssign = ref(false)
const savingMemberAssign = ref(false)

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
  code: '',
  start_date: null,
  end_date: null,
  total_target: 0,
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入产品名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择产品类型', trigger: 'change' }],
  code: [{ required: true, message: '请输入产品代码', trigger: 'blur' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
  total_target: [{ required: true, message: '请输入目标金额', trigger: 'blur' }]
}

const activeProducts = computed(() => {
  // 根据当前筛选状态返回非归档产品
  let filtered = products.value.filter(p => !p.is_archived)
  if (filterStatus.value) {
    filtered = filtered.filter(p => p.status === filterStatus.value)
  }
  return filtered
})

// 生成年份选项（从2024到当前年份）
const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  const startYear = 2024
  const years = []
  for (let year = currentYear; year >= startYear; year--) {
    years.push(year)
  }
  return years
})

const archivedProducts = computed(() => {
  // 根据选中年份筛选已归档产品
  return products.value.filter(p => {
    if (!p.is_archived) return false
    // 根据归档日期或结束日期判断年份
    const archiveDate = p.archived_at || p.end_date
    if (!archiveDate) return false
    const productYear = new Date(archiveDate).getFullYear()
    return productYear === archivedYear.value
  })
})

onMounted(() => {
  loadProducts()
})

async function loadProducts() {
  loading.value = true
  try {
    // 同时加载活跃产品和已归档产品
    const [activeRes, archivedRes] = await Promise.all([
      productsApi.list({ status: filterStatus.value, is_archived: false }),
      productsApi.list({ is_archived: true })
    ])
    // 合并结果，标记归档状态
    const activeProducts = activeRes.map(p => ({ ...p, is_archived: false }))
    const archivedProductsList = archivedRes.map(p => ({ ...p, is_archived: true, status: '已归档' }))
    products.value = [...activeProducts, ...archivedProductsList]
  } catch (error) {
    ElMessage.error('加载产品失败')
  } finally {
    loading.value = false
  }
}

// 任务分配相关计算属性
const groupAssignedTotal = computed(() => {
  return assignGroups.value.reduce((sum, g) => sum + (g.target || 0), 0)
})

const unassignedAmount = computed(() => {
  if (!assignProduct.value) return 0
  return Math.max(0, (assignProduct.value.total_target || 0) - groupAssignedTotal.value)
})

const assignProgress = computed(() => {
  if (!assignProduct.value || !assignProduct.value.total_target) return 0
  return Math.round((groupAssignedTotal.value / assignProduct.value.total_target) * 100)
})

const groupsWithTarget = computed(() => {
  return assignGroups.value.filter(g => (g.target || 0) > 0)
})

const selectedAssignGroup = computed(() => {
  return assignGroups.value.find(g => g.id === selectedGroupId.value)
})

const memberAssignedTotal = computed(() => {
  return selectedGroupMembers.value
    .filter(m => m.selected)
    .reduce((sum, m) => sum + (m.target || 0), 0)
})

const memberUnassigned = computed(() => {
  const groupTarget = selectedAssignGroup.value?.target || 0
  return Math.max(0, groupTarget - memberAssignedTotal.value)
})

// 任务分配相关方法
async function openAssignModal(product) {
  assignProduct.value = product
  assignStep.value = 1
  showAssignModal.value = true
  await loadGroupsForAssign()
}

async function loadGroupsForAssign() {
  try {
    const res = await groupsApi.list()
    groups.value = res

    // 获取已保存的营业部分配
    const savedAssignments = await productsApi.getGroupAssignments(assignProduct.value.id)

    // 初始化分配数据，使用已保存的值
    assignGroups.value = res.map(g => {
      const saved = savedAssignments.find(a => a.group_id === g.id)
      return {
        ...g,
        target: saved ? saved.target : 0,
        assigned: saved && saved.target > 0
      }
    })

    // 默认选择第一个营业部（不管是否有目标）
    if (assignGroups.value.length > 0) {
      selectedGroupId.value = assignGroups.value[0].id
      await onGroupChange(selectedGroupId.value)
    }
  } catch (error) {
    ElMessage.error('加载营业部数据失败')
  }
}

function updateGroupTarget(group) {
  group.assigned = (group.target || 0) > 0
}

function calculateGroupRatio(target) {
  if (!assignProduct.value || !assignProduct.value.total_target) return 0
  return Math.round(((target || 0) / assignProduct.value.total_target) * 100)
}

function getAssignStatusClass(target) {
  if (!target || target === 0) return 'status-pending'
  return 'status-assigned'
}

async function onGroupChange(groupId) {
  selectedGroupId.value = groupId
  selectedGroupMembers.value = []
  selectAllMembers.value = false
  try {
    // 获取该营业部的成员
    const membersRes = await membersApi.list(groupId, 'public_fund')

    // 获取已保存的个人分配
    const savedAssignments = await productsApi.getMemberAssignments(assignProduct.value.id, groupId)

    // 合并成员和分配数据
    selectedGroupMembers.value = membersRes.map(m => {
      const saved = savedAssignments.find(a => a.member_id === m.id)
      return {
        ...m,
        target: saved ? saved.target : 0,
        selected: saved && saved.target > 0
      }
    })

    selectAllMembers.value = selectedGroupMembers.value.every(m => m.selected)
  } catch (error) {
    ElMessage.error('加载成员数据失败')
  }
}

function toggleSelectAllMembers() {
  selectedGroupMembers.value.forEach(m => {
    m.selected = selectAllMembers.value
  })
}

function updateMemberTarget(member) {
  if (member.target > 0 && !member.selected) {
    member.selected = true
  }
}

function calculateMemberRatio(target) {
  const groupTarget = selectedAssignGroup.value?.target || 0
  if (!groupTarget) return 0
  return Math.round(((target || 0) / groupTarget) * 100)
}

function autoDistributeToMembers() {
  const groupTarget = selectedAssignGroup.value?.target || 0
  const selectedCount = selectedGroupMembers.value.filter(m => m.selected).length
  if (selectedCount === 0) {
    ElMessage.warning('请先选择要分配的成员')
    return
  }
  const avgTarget = Math.round((groupTarget / selectedCount) * 100) / 100
  selectedGroupMembers.value.forEach(m => {
    if (m.selected) {
      m.target = avgTarget
    }
  })
  ElMessage.success('已自动均分任务')
}

async function saveGroupAssign() {
  savingGroupAssign.value = true
  try {
    const assignments = assignGroups.value
      .filter(g => g.target > 0)
      .map(g => ({
        group_id: g.id,
        target: g.target
      }))
    await productsApi.saveGroupAssignments(assignProduct.value.id, {
      assignments
    })
    ElMessage.success('营业部分配保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    savingGroupAssign.value = false
  }
}

async function saveMemberAssign() {
  savingMemberAssign.value = true
  try {
    const assignments = selectedGroupMembers.value
      .filter(m => m.selected && m.target > 0)
      .map(m => ({
        member_id: m.id,
        target: m.target
      }))
    await productsApi.saveMemberAssignments(assignProduct.value.id, {
      group_id: selectedGroupId.value,
      assignments
    })
    ElMessage.success('个人分配保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    savingMemberAssign.value = false
  }
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const newProduct = await productsApi.create(form.value)
    ElMessage.success('产品创建成功')
    showDialog.value = false
    resetForm()
    await loadProducts()
    // 自动打开任务分配弹窗
    if (newProduct && newProduct.id) {
      openAssignModal(newProduct)
    }
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

async function handleUnarchive(product) {
  try {
    await ElMessageBox.confirm(
      `确定要解除归档产品 "${product.name}" 吗？`,
      '确认解除归档',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    await productsApi.unarchive(product.id)
    ElMessage.success('产品已解除归档')
    loadProducts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('解除归档失败')
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
  return Math.round((raised / product.total_target) * 100)
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
  if (!num && num !== 0) return '0'
  const rounded = Math.round(Number(num) * 10) / 10
  return rounded.toLocaleString('zh-CN', { maximumFractionDigits: 1 })
}

function formatDate(date) {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

// 清空产品销售数据
async function handleClearSalesData(product) {
  try {
    await ElMessageBox.confirm(
      `确定要清空产品 "${product.name}" 的所有销售数据吗？\n此操作将删除通过数据导入功能导入的所有Excel销售数据，不可恢复。`,
      '确认清空销售数据',
      {
        confirmButtonText: '确认清空',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    const res = await productsApi.clearSales(product.id)
    ElMessage.success(res.message)
    // 刷新产品列表
    await loadProducts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空销售数据失败:', error)
      ElMessage.error('清空销售数据失败: ' + (error.response?.data?.detail || error.message))
    }
  }
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
  align-items: center;
  gap: 8px;
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

/* Progress Stats Row - 目标销量和累积销量 */
.progress-stats-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  gap: 12px;
}

.progress-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.progress-stat-label {
  font-size: 12px;
  color: #6E6E73;
  font-weight: 500;
}

.progress-stat-value {
  font-size: 17px;
  font-weight: 700;
  color: #1D1D1F;
}

.progress-stat-value.actual {
  color: #34C759;
}

.progress-percentage {
  font-weight: 700;
  font-size: 16px;
  margin-left: auto;
}

.text-green { color: #34C759; }
.text-yellow { color: #FF9500; }
.text-orange { color: #FF7F00; }
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
.progress-yellow { background: #FF9500; }
.progress-orange { background: #FF7F00; }
.progress-gray { background: #8E8E93; }

.progress-footer {
  margin-top: 10px;
  font-size: 12px;
  color: #6E6E73;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.progress-assigned {
  color: #007AFF;
  font-weight: 600;
}

/* 清空数据按钮 */
.progress-footer .btn-link {
  font-size: 11px;
  padding: 4px 8px;
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
  margin-top: 0;
  padding-top: 0;
  border-top: none;
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

.archived-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.archived-code-tag {
  font-size: 11px;
  font-weight: 600;
  color: #5856D6;
  background: #EEEEFF;
  padding: 2px 8px;
  border-radius: 6px;
}
.archived-period {
  font-size: 12px;
  color: #6E6E73;
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

/* 任务分配弹窗样式 */
:deep(.assign-dialog .el-dialog__body) {
  padding: 20px 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.assign-modal-body {
  min-height: 400px;
}

.assign-summary {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background: #F5F5F7;
  border-radius: 12px;
}

.assign-summary-item {
  flex: 1;
  text-align: center;
}

.assign-summary-label {
  font-size: 12px;
  color: #6E6E73;
  margin-bottom: 6px;
}

.assign-summary-value {
  font-size: 20px;
  font-weight: 700;
  color: #1D1D1F;
}

.assign-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  padding: 4px;
  background: #F5F5F7;
  border-radius: 10px;
}

.assign-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  border: none;
  background: transparent;
  font-size: 14px;
  color: #6E6E73;
  cursor: pointer;
  transition: all 0.2s ease;
}

.assign-tab:hover {
  background: rgba(0, 0, 0, 0.04);
}

.assign-tab.active {
  background: white;
  color: #007AFF;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  font-weight: 600;
}

.assign-tab .tab-number {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #E5E5EA;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.assign-tab.active .tab-number {
  background: #007AFF;
  color: white;
}

.assign-step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.assign-step-title {
  font-weight: 600;
  color: #1D1D1F;
  font-size: 15px;
}

.assign-step-subtitle {
  font-size: 13px;
  color: #6E6E73;
}

.assign-table-wrapper {
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 16px;
}

.assign-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.assign-table th {
  background: #F5F5F7;
  padding: 12px 16px;
  font-weight: 600;
  color: #1D1D1F;
  text-align: left;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.assign-table td {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  color: #1D1D1F;
}

.assign-table tr:last-child td {
  border-bottom: none;
}

.assign-group-name {
  font-weight: 500;
  color: #1D1D1F;
}

.assign-group-leader {
  font-size: 12px;
  color: #6E6E73;
  margin-top: 4px;
}

.assign-member-info {
  display: flex;
  flex-direction: column;
}

.assign-member-name {
  font-weight: 500;
  color: #1D1D1F;
}

.assign-member-code {
  font-size: 12px;
  color: #6E6E73;
  margin-top: 2px;
}

.assign-status-tag {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.assign-status-tag.status-assigned {
  background: #E8F5E9;
  color: #34C759;
}

.assign-status-tag.status-pending {
  background: #FFF3E0;
  color: #FF9500;
}

.group-assign-overview {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px;
  background: #F5F5F7;
  border-radius: 10px;
  margin-bottom: 16px;
}

.overview-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.overview-label {
  font-size: 12px;
  color: #6E6E73;
}

.overview-value {
  font-size: 18px;
  font-weight: 700;
  color: #1D1D1F;
}

.overview-divider {
  width: 1px;
  height: 32px;
  background: rgba(0, 0, 0, 0.1);
}

.assign-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.assign-actions .btn-secondary {
  background: #F5F5F7;
  color: #1D1D1F;
}

.assign-actions .btn-secondary:hover {
  background: #E8E8ED;
}

.assign-actions .btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
