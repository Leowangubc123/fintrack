<template>
  <div class="advisory-target">
    <!-- Header -->
    <div class="view-header">
      <el-select v-model="selectedYear" style="width: 120px">
        <el-option v-for="year in years" :key="year" :label="year + '年'" :value="year" />
      </el-select>
      <el-button type="primary" @click="showBatchDialog = true">
        <el-icon><Plus /></el-icon>批量设置指标
      </el-button>
    </div>

    <!-- Targets Table - Apple Style -->
    <div class="targets-card">
      <div class="card-title">营业部考核指标</div>
      <div class="custom-table">
        <div class="table-head">
          <div class="th" style="width: 50px">序号</div>
          <div class="th" style="flex: 1">营业部</div>
          <div class="th" style="width: 120px" align="right">收入目标</div>
          <div class="th" style="width: 100px" align="right">户数目标</div>
          <div class="th" style="width: 100px" align="right">当前收入</div>
          <div class="th" style="width: 90px" align="right">签约户数</div>
          <div class="th" style="width: 100px" align="right">考核户数</div>
          <div class="th" style="width: 140px">收入完成率</div>
          <div class="th" style="width: 140px">户数完成率</div>
          <div class="th" style="width: 100px" align="center">操作</div>
        </div>
        <div
          v-for="(row, index) in tableData"
          :key="row.group_id"
          class="table-body-row"
          :class="{ selected: selectedGroupId === row.group_id, editing: editingRow === row.group_id }"
          @click="selectGroup(row.group_id)"
        >
          <div class="td" style="width: 50px" data-label="序号">{{ index + 1 }}</div>
          <div class="td" style="flex: 1" data-label="营业部">
            <span class="group-name">{{ row.group_name }}</span>
          </div>
          <div class="td" style="width: 120px" align="right" data-label="收入目标">
            <div v-if="editingRow === row.group_id" class="edit-field">
              <el-input-number v-model="editForm.income_target" :min="0" :precision="2" size="small" style="width: 110px" />
            </div>
            <span v-else>{{ row.income_target?.toFixed(2) || '0.00' }}万</span>
          </div>
          <div class="td" style="width: 100px" align="right" data-label="户数目标">
            <div v-if="editingRow === row.group_id" class="edit-field">
              <el-input-number v-model="editForm.households_target" :min="0" size="small" style="width: 90px" />
            </div>
            <span v-else>{{ row.households_target || 0 }}户</span>
          </div>
          <div class="td" style="width: 100px" align="right" data-label="当前收入">{{ row.current_income?.toFixed(2) || '0.00' }}万</div>
          <div class="td" style="width: 90px" align="right" data-label="签约户数">{{ row.current_households || 0 }}户</div>
          <div class="td" style="width: 100px" align="right" data-label="考核户数">
            <div v-if="editingRow === row.group_id" class="edit-field">
              <el-input-number v-model="editForm.assessed_households" :min="0" size="small" style="width: 90px" />
            </div>
            <span v-else>{{ row.assessed_households || 0 }}户</span>
          </div>
          <div class="td" style="width: 140px" data-label="收入完成率">
            <div class="rate-cell">
              <div class="rate-bar-bg">
                <div
                  class="rate-bar-fill"
                  :class="getProgressClass(row.income_rate)"
                  :style="{ width: Math.min(row.income_rate || 0, 100) + '%' }"
                />
              </div>
              <span class="rate-text" :class="getProgressClass(row.income_rate)">
                {{ row.income_rate || 0 }}%
              </span>
            </div>
          </div>
          <div class="td" style="width: 140px" data-label="户数完成率">
            <div class="rate-cell">
              <div class="rate-bar-bg">
                <div
                  class="rate-bar-fill"
                  :class="getProgressClass(row.households_rate)"
                  :style="{ width: Math.min(row.households_rate || 0, 100) + '%' }"
                />
              </div>
              <span class="rate-text" :class="getProgressClass(row.households_rate)">
                {{ row.households_rate || 0 }}%
              </span>
            </div>
          </div>
          <div class="td" style="width: 100px" align="center" data-label="操作" @click.stop>
            <div v-if="editingRow === row.group_id">
              <el-button type="primary" link size="small" @click="saveEdit(row)">保存</el-button>
              <el-button link size="small" @click="cancelEdit">取消</el-button>
            </div>
            <div v-else>
              <el-button type="primary" link size="small" @click="startEdit(row)">编辑</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Selected Group Subscription Details -->
    <div v-if="selectedGroupId" class="detail-card">
      <div class="detail-header">
        <div>
          <div class="detail-title">{{ selectedGroupName }} - 签约明细</div>
          <div class="detail-subtitle">点击列表项可编辑折算户数</div>
        </div>
        <div class="detail-search">
          <el-input v-model="detailSearch" placeholder="搜索员工" clearable style="width: 200px" size="small">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>

      <div class="subscription-list">
        <div
          v-for="row in paginatedGroupSubscriptions"
          :key="row.id"
          class="subscription-item"
          @click="openEditConverted(row)"
        >
          <div class="sub-main">
            <div class="sub-employee">{{ row.member_name }}</div>
            <div class="sub-product">
              <span class="product-tag">{{ row.product_type }}</span>
            </div>
            <div class="sub-date">{{ row.subscription_date }}</div>
          </div>
          <div class="sub-stats">
            <div class="sub-stat">
              <span class="sub-stat-label">签约资产</span>
              <span class="sub-stat-value">¥{{ ((row.asset_amount || 0) / 10000).toFixed(1) }}万</span>
            </div>
            <div class="sub-stat">
              <span class="sub-stat-label">原始户数</span>
              <span class="sub-stat-value">{{ row.original_households }}户</span>
            </div>
            <div class="sub-stat">
              <span class="sub-stat-label">折算户数</span>
              <span
                class="sub-stat-value"
                :class="{ modified: row.converted_households !== row.original_households }"
              >
                {{ row.converted_households }}户
              </span>
            </div>
            <div v-if="row.conversion_note" class="sub-note">
              {{ row.conversion_note }}
            </div>
          </div>
          <div class="sub-action">
            <el-button type="primary" link size="small" @click.stop="openEditConverted(row)">编辑</el-button>
          </div>
        </div>
        <div v-if="paginatedGroupSubscriptions.length === 0" class="detail-empty">
          暂无签约明细
        </div>
      </div>

      <el-pagination
        v-if="filteredGroupSubscriptions.length > detailPageSize"
        v-model:current-page="detailPage"
        v-model:page-size="detailPageSize"
        :total="filteredGroupSubscriptions.length"
        layout="prev, pager, next"
        small
        class="detail-pagination"
      />
    </div>

    <!-- Edit Converted Households Dialog -->
    <el-dialog v-model="showEditDialog" title="编辑折算户数" width="500px">
      <div v-if="editingSubscription" class="edit-form">
        <el-form label-width="100px">
          <el-form-item label="营业部">
            <span>{{ editingSubscription.group_name }}</span>
          </el-form-item>
          <el-form-item label="员工">
            <span>{{ editingSubscription.member_name }}</span>
          </el-form-item>
          <el-form-item label="产品类型">
            <span>{{ editingSubscription.product_type }}</span>
          </el-form-item>
          <el-form-item label="签约资产">
            <span>¥{{ ((editingSubscription.asset_amount || 0) / 10000).toFixed(1) }}万</span>
          </el-form-item>
          <el-form-item label="原始户数">
            <span>{{ editingSubscription.original_households }}户</span>
          </el-form-item>
          <el-form-item label="折算户数">
            <el-input-number v-model="editConvertedForm.converted_households" :min="0" style="width: 150px" />
            <div class="form-tip">根据资产规模调整实际考核户数</div>
          </el-form-item>
          <el-form-item label="折算说明">
            <el-input
              v-model="editConvertedForm.conversion_note"
              type="textarea"
              :rows="2"
              placeholder="请输入折算原因（可选）"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveConverted">保存</el-button>
      </template>
    </el-dialog>

    <!-- Batch Set Targets Dialog -->
    <el-dialog v-model="showBatchDialog" title="批量设置考核指标" width="500px">
      <el-form label-width="100px">
        <el-form-item label="营业部">
          <el-select v-model="batchForm.group_id" placeholder="选择营业部" style="width: 100%">
            <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
          <div class="form-tip">不选择则设置所有营业部</div>
        </el-form-item>
        <el-form-item label="收入目标">
          <el-input-number v-model="batchForm.income_target" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="户数目标">
          <el-input-number v-model="batchForm.households_target" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="考核户数">
          <el-input-number v-model="batchForm.assessed_households" :min="0" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchDialog = false">取消</el-button>
        <el-button type="primary" @click="saveBatchTargets">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { advisoryApi } from '../../api/advisory.js'
import { groupsApi } from '../../api/index.js'

const selectedYear = ref(new Date().getFullYear())
const years = computed(() => {
  const current = new Date().getFullYear()
  return [current, current + 1]
})

const groups = ref([])
const targets = ref([])
const subscriptions = ref([])
const loading = ref(false)

const editingRow = ref(null)
const editForm = ref({
  income_target: 0,
  households_target: 0,
  assessed_households: 0
})

const showBatchDialog = ref(false)
const batchForm = ref({
  group_id: null,
  income_target: 0,
  households_target: 0,
  assessed_households: 0
})

const selectedGroupId = ref(null)
const detailSearch = ref('')
const detailPage = ref(1)
const detailPageSize = ref(8)

const showEditDialog = ref(false)
const editingSubscription = ref(null)
const editConvertedForm = ref({
  converted_households: 1,
  conversion_note: ''
})

const fetchGroups = async () => {
  try {
    const res = await groupsApi.list()
    groups.value = res
  } catch (error) {
    console.error('Failed to fetch groups:', error)
  }
}

const fetchTargets = async () => {
  loading.value = true
  try {
    const res = await advisoryApi.getTargets({
      year: selectedYear.value
    })
    targets.value = res || []
  } catch (error) {
    console.error('Failed to fetch targets:', error)
  } finally {
    loading.value = false
  }
}

const fetchSubscriptions = async () => {
  try {
    const res = await advisoryApi.getSubscriptions({
      year: selectedYear.value,
      page_size: 10000
    })
    subscriptions.value = res.items || []
  } catch (error) {
    console.error('Failed to fetch subscriptions:', error)
  }
}

const calculateCurrentStats = (groupId) => {
  const groupSubs = subscriptions.value.filter(s => s.group_id === groupId)
  const income = groupSubs.reduce((sum, s) => sum + parseFloat(s.advisory_income || 0), 0) / 10000
  const households = groupSubs.reduce((sum, s) => sum + (s.converted_households || 1), 0)
  return { income, households }
}

const tableData = computed(() => {
  return groups.value.map(group => {
    const target = targets.value.find(t => t.group_id === group.id) || {}
    const current = calculateCurrentStats(group.id)
    const incomeRate = target.income_target > 0
      ? Math.round((current.income / target.income_target) * 100)
      : 0
    const assessedHouseholds = target.assessed_households || 0
    const householdsRate = target.households_target > 0
      ? Math.round((assessedHouseholds / target.households_target) * 100)
      : 0

    return {
      group_id: group.id,
      group_name: group.name,
      income_target: target.income_target || 0,
      households_target: target.households_target || 0,
      assessed_households: assessedHouseholds,
      current_income: current.income,
      current_households: current.households,
      income_rate: incomeRate,
      households_rate: householdsRate
    }
  })
})

const selectedGroupName = computed(() => {
  const group = groups.value.find(g => g.id === selectedGroupId.value)
  return group ? group.name : ''
})

const filteredGroupSubscriptions = computed(() => {
  let data = subscriptions.value.filter(s => s.group_id === selectedGroupId.value)
  if (detailSearch.value) {
    const search = detailSearch.value.toLowerCase()
    data = data.filter(s => s.member_name.toLowerCase().includes(search))
  }
  return data.sort((a, b) => new Date(b.subscription_date) - new Date(a.subscription_date))
})

const paginatedGroupSubscriptions = computed(() => {
  const start = (detailPage.value - 1) * detailPageSize.value
  return filteredGroupSubscriptions.value.slice(start, start + detailPageSize.value)
})

const selectGroup = (groupId) => {
  if (editingRow.value) return
  selectedGroupId.value = selectedGroupId.value === groupId ? null : groupId
  detailPage.value = 1
}

const startEdit = (row) => {
  editingRow.value = row.group_id
  editForm.value = {
    income_target: row.income_target,
    households_target: row.households_target,
    assessed_households: row.assessed_households
  }
}

const cancelEdit = () => {
  editingRow.value = null
}

const saveEdit = async (row) => {
  try {
    await advisoryApi.saveTarget({
      group_id: row.group_id,
      year: selectedYear.value,
      income_target: editForm.value.income_target,
      households_target: editForm.value.households_target,
      assessed_households: editForm.value.assessed_households
    })
    ElMessage.success('保存成功')
    editingRow.value = null
    fetchTargets()
  } catch (error) {
    console.error('Save error:', error)
    ElMessage.error('保存失败')
  }
}

const saveBatchTargets = async () => {
  try {
    if (batchForm.value.group_id) {
      await advisoryApi.saveTarget({
        group_id: batchForm.value.group_id,
        year: selectedYear.value,
        income_target: batchForm.value.income_target,
        households_target: batchForm.value.households_target,
        assessed_households: batchForm.value.assessed_households
      })
    } else {
      for (const group of groups.value) {
        await advisoryApi.saveTarget({
          group_id: group.id,
          year: selectedYear.value,
          income_target: batchForm.value.income_target,
          households_target: batchForm.value.households_target,
          assessed_households: batchForm.value.assessed_households
        })
      }
    }
    ElMessage.success('批量设置成功')
    showBatchDialog.value = false
    fetchTargets()
  } catch (error) {
    console.error('Batch save error:', error)
    ElMessage.error('保存失败')
  }
}

const openEditConverted = (row) => {
  editingSubscription.value = row
  editConvertedForm.value = {
    converted_households: row.converted_households || row.original_households || 1,
    conversion_note: row.conversion_note || ''
  }
  showEditDialog.value = true
}

const saveConverted = async () => {
  try {
    await advisoryApi.updateSubscription(editingSubscription.value.id, {
      converted_households: editConvertedForm.value.converted_households,
      conversion_note: editConvertedForm.value.conversion_note
    })
    ElMessage.success('保存成功')
    showEditDialog.value = false
    fetchSubscriptions()
    fetchTargets()
  } catch (error) {
    console.error('Save error:', error)
    ElMessage.error('保存失败')
  }
}

const getProgressClass = (rate) => {
  if (rate >= 100) return 'success'
  if (rate >= 50) return 'warning'
  return 'danger'
}

watch(selectedYear, () => {
  fetchTargets()
  fetchSubscriptions()
  selectedGroupId.value = null
})

const refreshAll = () => {
  fetchTargets()
  fetchSubscriptions()
}

onMounted(() => {
  fetchGroups()
  fetchTargets()
  fetchSubscriptions()
  window.addEventListener('advisory-data-imported', refreshAll)
})

onBeforeUnmount(() => {
  window.removeEventListener('advisory-data-imported', refreshAll)
})
</script>

<style scoped>
.advisory-target {
  padding: 0;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.view-header :deep(.el-button--primary) {
  background: #1EAEDB;
  border-color: #1EAEDB;
}

.targets-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
  padding: 24px;
  margin-bottom: 20px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16px;
}

/* Custom Apple-style Table */
.custom-table {
  width: 100%;
}

.table-head {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background: #F9FAFB;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #6B7280;
  margin-bottom: 6px;
}

.table-body-row {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  border-radius: 8px;
  font-size: 14px;
  color: #111827;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid transparent;
}

.table-body-row:hover {
  background: #F8FAFC;
}

.table-body-row.selected {
  background: #EFF6FF;
  border-color: #BFDBFE;
}

.table-body-row.editing {
  background: #FFFBEB;
  cursor: default;
}

.th,
.td {
  padding: 0 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.th:first-child,
.td:first-child {
  padding-left: 0;
}

.th:last-child,
.td:last-child {
  padding-right: 0;
}

.group-name {
  font-weight: 500;
}

.edit-field {
  display: flex;
  justify-content: flex-end;
}

.rate-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rate-bar-bg {
  flex: 1;
  height: 6px;
  background: #F3F4F6;
  border-radius: 3px;
  overflow: hidden;
  min-width: 60px;
}

.rate-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.rate-bar-fill.success {
  background: #10B981;
}

.rate-bar-fill.warning {
  background: #F59E0B;
}

.rate-bar-fill.danger {
  background: #EF4444;
}

.rate-text {
  font-size: 13px;
  font-weight: 600;
  min-width: 44px;
  text-align: right;
}

.rate-text.success {
  color: #10B981;
}

.rate-text.warning {
  color: #F59E0B;
}

.rate-text.danger {
  color: #EF4444;
}

/* Detail Card */
.detail-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
  padding: 24px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.detail-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.detail-subtitle {
  font-size: 13px;
  color: #6B7280;
  margin-top: 4px;
}

.detail-search {
  flex-shrink: 0;
}

.subscription-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.subscription-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: #FAFAFB;
  border-radius: 10px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
}

.subscription-item:hover {
  background: #F1F5F9;
  border-color: #E2E8F0;
}

.sub-main {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.sub-employee {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  width: 90px;
  flex-shrink: 0;
}

.sub-product {
  width: 100px;
  flex-shrink: 0;
}

.sub-date {
  font-size: 14px;
  color: #6B7280;
  width: 110px;
  flex-shrink: 0;
}

.product-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 12px;
  background: #EFF6FF;
  color: #1EAEDB;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.sub-stats {
  display: flex;
  align-items: center;
  gap: 28px;
  flex-shrink: 0;
}

.sub-stat {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  min-width: 70px;
}

.sub-stat-label {
  font-size: 12px;
  color: #9CA3AF;
}

.sub-stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.sub-stat-value.modified {
  color: #1EAEDB;
}

.sub-note {
  font-size: 12px;
  color: #6B7280;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sub-action {
  margin-left: 16px;
  flex-shrink: 0;
}

.detail-empty {
  padding: 40px 0;
  text-align: center;
  color: #9CA3AF;
  font-size: 14px;
}

.detail-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

.form-tip {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 4px;
}

:deep(.el-dialog__header) {
  font-weight: 600;
}

@media (max-width: 1100px) {
  .sub-main {
    flex-wrap: wrap;
    gap: 8px 16px;
  }

  .sub-stats {
    flex-wrap: wrap;
    gap: 12px 20px;
    justify-content: flex-end;
  }

  .subscription-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .sub-action {
    margin-left: 0;
    align-self: flex-end;
  }
}

@media (max-width: 900px) {
  .table-head {
    display: none;
  }

  .table-body-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    padding: 16px;
    margin-bottom: 8px;
    border: 1px solid #F3F4F6;
  }

  .table-body-row.selected {
    border-color: #BFDBFE;
  }

  .td {
    width: 100% !important;
    padding: 0;
    display: flex;
    justify-content: space-between;
  }

  .td::before {
    content: attr(data-label);
    font-weight: 500;
    color: #6B7280;
    font-size: 13px;
  }

  .rate-cell {
    width: 100%;
  }
}
</style>
