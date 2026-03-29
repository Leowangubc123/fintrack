<template>
  <div class="sales-entry">
    <!-- 录入类型切换 -->
    <div class="entry-tabs">
      <div
        class="entry-tab sale"
        :class="{ active: entryType === 'sale' }"
        @click="entryType = 'sale'"
      >
        <el-icon><TrendCharts /></el-icon> 销售录入
      </div>
      <div
        class="entry-tab redeem"
        :class="{ active: entryType === 'redeem' }"
        @click="entryType = 'redeem'"
      >
        <el-icon><Money /></el-icon> 赎回录入
      </div>
    </div>

    <div class="entry-container">
      <!-- 左侧：录入表单 -->
      <div class="form-panel">
        <div class="panel-title">{{ entryType === 'sale' ? '录入销售记录' : '录入赎回记录' }}</div>
        <el-form :model="form" label-position="top">
          <el-form-item label="选择产品" required>
            <el-select
              v-model="form.product_id"
              placeholder="请选择私募产品"
              style="width: 100%"
              filterable
              @change="onProductChange"
            >
              <el-option
                v-for="product in products"
                :key="product.id"
                :label="`${product.name} (${product.code})`"
                :value="product.id"
              />
            </el-select>
          </el-form-item>

          <!-- 销售录入特有：销售系数 -->
          <el-form-item v-if="entryType === 'sale'" label="销售系数">
            <div class="coefficient-display">
              <span class="coefficient-label">该产品销售系数</span>
              <span class="coefficient-value">{{ selectedProduct?.sales_coefficient || '-' }}</span>
            </div>
          </el-form-item>

          <el-form-item label="营业部" required>
            <el-select
              v-model="selectedGroupId"
              placeholder="请选择营业部"
              style="width: 100%"
              filterable
              @change="onGroupChange"
            >
              <el-option
                v-for="group in groups"
                :key="group.id"
                :label="group.name"
                :value="group.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="销售人员" required>
            <el-select
              v-model="form.member_id"
              placeholder="请先选择营业部"
              style="width: 100%"
              filterable
              :disabled="!selectedGroupId"
            >
              <el-option
                v-for="member in filteredMembers"
                :key="member.id"
                :label="member.name"
                :value="member.id"
              />
            </el-select>
          </el-form-item>

          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="日期" required>
                <el-date-picker
                  v-model="form.transaction_date"
                  type="date"
                  placeholder="选择日期"
                  style="width: 100%"
                  value-format="YYYY-MM-DD"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="entryType === 'sale' ? '实际销量(万)' : '赎回金额(万)'" required>
                <el-input-number
                  v-model="form.amount"
                  :min="0"
                  :precision="2"
                  :step="10"
                  style="width: 100%"
                  @change="onAmountChange"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="备注">
            <el-input
              v-model="form.remark"
              type="textarea"
              :rows="2"
              placeholder="可选填写备注信息"
            />
          </el-form-item>

          <!-- 销售录入特有：考核销量计算 -->
          <div v-if="entryType === 'sale'" class="assessed-display">
            <div class="assessed-label">考核销量（自动计算）</div>
            <div class="assessed-value">{{ calculatedAssessedAmount }} 万</div>
            <div class="assessed-hint">实际销量 × 销售系数 = 考核销量</div>
          </div>

          <!-- 赎回录入特有：赎回金额显示 -->
          <div v-else class="redeem-display">
            <div class="redeem-label">赎回金额</div>
            <div class="redeem-value">{{ form.amount || 0 }} 万</div>
            <div class="redeem-hint">将从保有统计中扣除该赎回金额</div>
          </div>

          <el-button
            type="primary"
            size="large"
            style="width: 100%; margin-top: 20px"
            :class="entryType === 'redeem' ? 'redeem-btn' : ''"
            @click="submitForm"
          >
            {{ entryType === 'sale' ? '提交销售记录' : '提交赎回记录' }}
          </el-button>
        </el-form>
      </div>

      <!-- 右侧：最近记录 -->
      <div class="form-panel">
        <div class="panel-title">最近操作记录</div>
        <div class="record-list">
          <div
            v-for="record in recentRecords"
            :key="record.id"
            class="record-item"
          >
            <div class="record-icon" :class="record.transaction_type">
              {{ record.transaction_type === 'sale' ? '📈' : '📉' }}
            </div>
            <div class="record-content">
              <div class="record-product">{{ record.product_name }}</div>
              <div class="record-meta">
                {{ record.member_name }} · {{ record.group_name }} · {{ formatDate(record.transaction_date) }}
              </div>
            </div>
            <div class="record-amount">
              <div class="record-actual">{{ record.amount }}万</div>
              <div v-if="record.transaction_type === 'sale'" class="record-assessed">
                {{ record.assessed_amount }}万
              </div>
              <div v-else class="record-redeem">赎回</div>
              <div class="record-label">
                {{ record.transaction_type === 'sale' ? `销售 系数${record.sales_coefficient}` : '赎回' }}
              </div>
            </div>
            <el-button
              type="danger"
              link
              size="small"
              class="delete-btn"
              @click="deleteRecord(record.id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { TrendCharts, Money, Delete } from '@element-plus/icons-vue'
import { privateFundApi, groupsApi, membersApi } from '../../api'

const entryType = ref('sale') // 'sale' 或 'redeem'
const products = ref([])
const groups = ref([])
const members = ref([])
const selectedGroupId = ref(null)
const recentRecords = ref([])

const form = ref({
  product_id: null,
  member_id: null,
  transaction_date: new Date().toISOString().split('T')[0],
  amount: null,
  remark: ''
})

const selectedProduct = computed(() => {
  return products.value.find(p => p.id === form.value.product_id)
})

const filteredMembers = computed(() => {
  if (!selectedGroupId.value) return []
  return members.value.filter(m => m.group_id === selectedGroupId.value)
})

const calculatedAssessedAmount = computed(() => {
  if (!form.value.amount || !selectedProduct.value) return '0.0'
  return (form.value.amount * selectedProduct.value.sales_coefficient).toFixed(1)
})

const onProductChange = () => {
  // 产品选择变化时自动更新销售系数显示
}

const onGroupChange = () => {
  // 切换营业部时，清空已选员工
  form.value.member_id = null
}

const onAmountChange = () => {
  // 金额变化时自动计算
}

const submitForm = async () => {
  try {
    if (!form.value.product_id || !form.value.member_id || !form.value.amount) {
      ElMessage.warning('请填写完整信息')
      return
    }

    const data = {
      ...form.value,
      transaction_type: entryType.value,
      sales_coefficient: entryType.value === 'sale' ? selectedProduct.value?.sales_coefficient : null,
      assessed_amount: entryType.value === 'sale' ? parseFloat(calculatedAssessedAmount.value) : null
    }

    await privateFundApi.createTransaction(data)
    ElMessage.success(entryType.value === 'sale' ? '销售记录提交成功' : '赎回记录提交成功')

    // 重置表单
    form.value = {
      product_id: null,
      member_id: null,
      transaction_date: new Date().toISOString().split('T')[0],
      amount: null,
      remark: ''
    }

    // 刷新记录列表
    loadRecentRecords()
  } catch (error) {
    ElMessage.error('提交失败')
  }
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}-${date.getDate()}`
}

const loadProducts = async () => {
  try {
    const res = await privateFundApi.getProducts()
    products.value = res
  } catch (error) {
    ElMessage.error('加载产品列表失败')
  }
}

const loadGroups = async () => {
  try {
    const res = await groupsApi.list()
    groups.value = res
  } catch (error) {
    ElMessage.error('加载营业部列表失败')
  }
}

const loadMembers = async () => {
  try {
    const res = await membersApi.getAll()
    members.value = res
  } catch (error) {
    ElMessage.error('加载营销人员列表失败')
  }
}

const loadRecentRecords = async () => {
  try {
    const res = await privateFundApi.getRecentTransactions(10)
    recentRecords.value = res
  } catch (error) {
    ElMessage.error('加载最近记录失败')
  }
}

const deleteRecord = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条记录吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await privateFundApi.deleteTransaction(id)
    ElMessage.success('删除成功')
    loadRecentRecords()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

watch(entryType, () => {
  // 切换类型时重置表单
  form.value = {
    product_id: null,
    member_id: null,
    transaction_date: new Date().toISOString().split('T')[0],
    amount: null,
    remark: ''
  }
  selectedGroupId.value = null
})

onMounted(() => {
  loadProducts()
  loadGroups()
  loadMembers()
  loadRecentRecords()
})
</script>

<style scoped>
.sales-entry {
  padding: 24px;
}

.entry-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.entry-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: white;
  color: #6E6E73;
}

.entry-tab:hover {
  background: #F5F5F7;
}

.entry-tab.sale {
  color: #7C3AED;
}

.entry-tab.sale.active {
  background: linear-gradient(135deg, #7C3AED 0%, #A855F7 100%);
  color: white;
  border-color: transparent;
}

.entry-tab.redeem {
  color: #34C759;
}

.entry-tab.redeem.active {
  background: linear-gradient(135deg, #34C759 0%, #30D158 100%);
  color: white;
  border-color: transparent;
}

.entry-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.form-panel {
  background: white;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  padding: 24px;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.coefficient-display {
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.08) 0%, rgba(168, 85, 247, 0.08) 100%);
  border: 1px solid rgba(124, 58, 237, 0.2);
  border-radius: 10px;
  padding: 12px 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

.coefficient-label {
  font-size: 14px;
  color: #6E6E73;
}

.coefficient-value {
  font-size: 24px;
  font-weight: 700;
  color: #7C3AED;
}

.assessed-display {
  background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
  border-radius: 12px;
  padding: 20px;
  margin-top: 20px;
  color: white;
}

.assessed-label {
  font-size: 13px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.assessed-value {
  font-size: 32px;
  font-weight: 700;
}

.assessed-hint {
  font-size: 12px;
  opacity: 0.8;
  margin-top: 4px;
}

.redeem-display {
  background: linear-gradient(135deg, #FF3B30 0%, #FF6B35 100%);
  border-radius: 12px;
  padding: 20px;
  margin-top: 20px;
  color: white;
}

.redeem-label {
  font-size: 13px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.redeem-value {
  font-size: 32px;
  font-weight: 700;
}

.redeem-hint {
  font-size: 12px;
  opacity: 0.8;
  margin-top: 4px;
}

.redeem-btn {
  background: linear-gradient(135deg, #34C759 0%, #30D158 100%) !important;
  border: none !important;
}

.redeem-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(52, 199, 89, 0.3);
}

.record-list {
  max-height: 600px;
  overflow-y: auto;
}

.record-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  transition: background 0.2s;
}

.record-item:hover {
  background: #FAFAFB;
}

.record-item:last-child {
  border-bottom: none;
}

.record-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 14px;
  font-size: 18px;
}

.record-icon.sale {
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
}

.record-icon.redeem {
  background: linear-gradient(135deg, rgba(255, 59, 48, 0.1) 0%, rgba(255, 107, 53, 0.1) 100%);
}

.record-content {
  flex: 1;
}

.record-product {
  font-size: 15px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 2px;
}

.record-meta {
  font-size: 13px;
  color: #8E8E93;
}

.record-amount {
  text-align: right;
}

.record-actual {
  font-size: 14px;
  color: #1D1D1F;
  font-weight: 500;
}

.record-assessed {
  font-size: 16px;
  font-weight: 700;
  color: #007AFF;
}

.record-redeem {
  font-size: 16px;
  font-weight: 700;
  color: #FF3B30;
}

.record-label {
  font-size: 11px;
  color: #8E8E93;
}

.delete-btn {
  margin-left: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.record-item:hover .delete-btn {
  opacity: 1;
}
</style>
