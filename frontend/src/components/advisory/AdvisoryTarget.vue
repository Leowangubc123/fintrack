<template>
  <div class="advisory-target">
    <!-- Header with year selector -->
    <div class="view-header">
      <el-select v-model="selectedYear" style="width: 120px">
        <el-option v-for="year in years" :key="year" :label="year + '年'" :value="year" />
      </el-select>
      <el-button type="primary" @click="showBatchDialog = true">
        <el-icon><Plus /></el-icon>批量设置指标
      </el-button>
    </div>

    <!-- Targets Table -->
    <div class="table-container">
      <el-table :data="tableData" stripe v-loading="loading">
        <el-table-column type="index" label="序号" width="60" />

        <el-table-column prop="group_name" label="营业部" min-width="150" />

        <el-table-column label="收入目标" align="right" width="150">
          <template #default="{ row }">
            <div v-if="editingRow === row.group_id" class="edit-field">
              <el-input-number v-model="editForm.income_target" :min="0" :precision="2" size="small" style="width: 120px" />
            </div>
            <span v-else>{{ row.income_target?.toFixed(2) || '0.00' }}万</span>
          </template>
        </el-table-column>

        <el-table-column label="户数目标" align="right" width="120">
          <template #default="{ row }">
            <div v-if="editingRow === row.group_id" class="edit-field">
              <el-input-number v-model="editForm.households_target" :min="0" size="small" style="width: 100px" />
            </div>
            <span v-else>{{ row.households_target || 0 }}户</span>
          </template>
        </el-table-column>

        <el-table-column label="当前收入" align="right" width="120">
          <template #default="{ row }">
            <span>{{ row.current_income?.toFixed(2) || '0.00' }}万</span>
          </template>
        </el-table-column>

        <el-table-column label="当前户数" align="right" width="100">
          <template #default="{ row }">
            <span>{{ row.current_households || 0 }}户</span>
          </template>
        </el-table-column>

        <el-table-column label="收入完成率" align="center" width="120">
          <template #default="{ row }">
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
          </template>
        </el-table-column>

        <el-table-column label="户数完成率" align="center" width="120">
          <template #default="{ row }">
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
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <div v-if="editingRow === row.group_id">
              <el-button type="primary" link size="small" @click="saveEdit(row)">保存</el-button>
              <el-button link size="small" @click="cancelEdit">取消</el-button>
            </div>
            <div v-else>
              <el-button type="primary" link size="small" @click="startEdit(row)">编辑</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
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
            <span>{{ editingSubscription.asset_amount }}万</span>
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
          <template #append>万元</template>
        </el-form-item>
        <el-form-item label="户数目标">
          <el-input-number v-model="batchForm.households_target" :min="0" style="width: 100%" />
          <template #append>户</template>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchDialog = false">取消</el-button>
        <el-button type="primary" @click="saveBatchTargets">保存</el-button>
      </template>
    </el-dialog>

    <!-- Detail Section -->
    <div class="detail-section">
      <div class="detail-header">
        <span class="detail-title">签约明细 - 折算户数编辑</span>
        <div class="detail-filters">
          <el-select v-model="detailFilterGroup" placeholder="营业部" clearable style="width: 140px">
            <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
          <el-input v-model="detailSearch" placeholder="搜索员工" clearable style="width: 160px" />
        </div>
      </div>

      <el-table :data="paginatedSubscriptions" size="small" stripe max-height="400">
        <el-table-column prop="group_name" label="营业部" width="140" />
        <el-table-column prop="member_name" label="员工" width="100" />
        <el-table-column prop="product_type" label="产品" width="80" />
        <el-table-column prop="subscription_date" label="签约日期" width="110" />
        <el-table-column prop="asset_amount" label="资产(万)" width="90" align="right" />
        <el-table-column prop="original_households" label="原始户数" width="90" align="center" />
        <el-table-column prop="converted_households" label="折算户数" width="90" align="center">
          <template #default="{ row }">
            <span :class="{ 'modified': row.converted_households !== row.original_households }">
              {{ row.converted_households }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="conversion_note" label="折算说明" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEditConverted(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="detailPage"
        v-model:page-size="detailPageSize"
        :total="filteredSubscriptions.length"
        layout="prev, pager, next"
        small
        class="detail-pagination"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
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
  households_target: 0
})

const showBatchDialog = ref(false)
const batchForm = ref({
  group_id: null,
  income_target: 0,
  households_target: 0
})

const detailFilterGroup = ref(null)
const detailSearch = ref('')
const detailPage = ref(1)
const detailPageSize = ref(10)

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
    const householdsRate = target.households_target > 0
      ? Math.round((current.households / target.households_target) * 100)
      : 0

    return {
      group_id: group.id,
      group_name: group.name,
      income_target: target.income_target || 0,
      households_target: target.households_target || 0,
      current_income: current.income,
      current_households: current.households,
      income_rate: incomeRate,
      households_rate: householdsRate
    }
  })
})

const filteredSubscriptions = computed(() => {
  let data = subscriptions.value
  if (detailFilterGroup.value) {
    data = data.filter(s => s.group_id === detailFilterGroup.value)
  }
  if (detailSearch.value) {
    const search = detailSearch.value.toLowerCase()
    data = data.filter(s => s.member_name.toLowerCase().includes(search))
  }
  return data
})

const paginatedSubscriptions = computed(() => {
  const start = (detailPage.value - 1) * detailPageSize.value
  return filteredSubscriptions.value.slice(start, start + detailPageSize.value)
})

const startEdit = (row) => {
  editingRow.value = row.group_id
  editForm.value = {
    income_target: row.income_target,
    households_target: row.households_target
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
      households_target: editForm.value.households_target
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
      // Single group
      await advisoryApi.saveTarget({
        group_id: batchForm.value.group_id,
        year: selectedYear.value,
        income_target: batchForm.value.income_target,
        households_target: batchForm.value.households_target
      })
    } else {
      // All groups
      for (const group of groups.value) {
        await advisoryApi.saveTarget({
          group_id: group.id,
          year: selectedYear.value,
          income_target: batchForm.value.income_target,
          households_target: batchForm.value.households_target
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
})

onMounted(() => {
  fetchGroups()
  fetchTargets()
  fetchSubscriptions()
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

.table-container {
  background: white;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
  overflow: hidden;
  margin-bottom: 24px;
}

:deep(.el-table th) {
  background: #F9FAFB;
  font-weight: 600;
  color: #374151;
}

.edit-field {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.rate-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rate-bar-bg {
  flex: 1;
  height: 6px;
  background: #F3F4F6;
  border-radius: 3px;
  overflow: hidden;
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
  font-size: 12px;
  font-weight: 600;
  min-width: 40px;
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

.detail-section {
  background: white;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
  padding: 20px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.detail-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.detail-filters {
  display: flex;
  gap: 12px;
}

.form-tip {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 4px;
}

.modified {
  color: #0891B2;
  font-weight: 600;
}

.detail-pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>