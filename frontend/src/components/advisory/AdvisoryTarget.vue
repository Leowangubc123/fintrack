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

    <!-- Targets Table -->
    <div class="targets-card">
      <div class="card-title">营业部考核指标</div>
      <div class="custom-table">
        <div class="table-head">
          <div class="th" style="width: 50px">序号</div>
          <div class="th" style="flex: 1">营业部</div>
          <div class="th" style="width: 130px" align="right">收入考核指标(万)</div>
          <div class="th" style="width: 130px" align="right">投顾收入情况(万)</div>
          <div class="th" style="width: 140px">收入完成率</div>
          <div class="th" style="width: 110px" align="right">户数考核指标</div>
          <div class="th" style="width: 110px" align="right">户数情况</div>
          <div class="th" style="width: 140px">户数完成率</div>
          <div class="th" style="width: 100px" align="center">操作</div>
        </div>
        <div
          v-for="(row, index) in tableData"
          :key="row.group_id"
          class="table-body-row"
          :class="{ editing: editingRow === row.group_id }"
        >
          <div class="td" style="width: 50px" data-label="序号">{{ index + 1 }}</div>
          <div class="td" style="flex: 1" data-label="营业部">
            <span class="group-name">{{ row.group_name }}</span>
          </div>
          <div class="td" style="width: 130px" align="right" data-label="收入考核指标(万)">
            <div v-if="editingRow === row.group_id" class="edit-field">
              <el-input-number v-model="editForm.income_target" :min="0" :precision="2" size="small" style="width: 115px" />
            </div>
            <span v-else>{{ row.income_target?.toFixed(2) || '0.00' }}</span>
          </div>
          <div class="td" style="width: 130px" align="right" data-label="投顾收入情况(万)">
            <div v-if="editingRow === row.group_id" class="edit-field">
              <el-input-number v-model="editForm.current_income" :min="0" :precision="2" size="small" style="width: 115px" />
            </div>
            <span v-else>{{ row.current_income?.toFixed(2) || '0.00' }}</span>
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
          <div class="td" style="width: 110px" align="right" data-label="户数考核指标">
            <div v-if="editingRow === row.group_id" class="edit-field">
              <el-input-number v-model="editForm.households_target" :min="0" size="small" style="width: 100px" />
            </div>
            <span v-else>{{ row.households_target || 0 }}</span>
          </div>
          <div class="td" style="width: 110px" align="right" data-label="户数情况">
            <div v-if="editingRow === row.group_id" class="edit-field">
              <el-input-number v-model="editForm.current_households" :min="0" size="small" style="width: 100px" />
            </div>
            <span v-else>{{ row.current_households || 0 }}</span>
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

    <!-- Batch Set Targets Dialog -->
    <el-dialog v-model="showBatchDialog" title="批量设置考核指标" width="500px">
      <el-form label-width="120px">
        <el-form-item label="营业部">
          <el-select v-model="batchForm.group_id" placeholder="选择营业部" style="width: 100%">
            <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
          <div class="form-tip">不选择则设置所有营业部</div>
        </el-form-item>
        <el-form-item label="收入考核指标(万)">
          <el-input-number v-model="batchForm.income_target" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="投顾收入情况(万)">
          <el-input-number v-model="batchForm.current_income" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="户数考核指标">
          <el-input-number v-model="batchForm.households_target" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="户数情况">
          <el-input-number v-model="batchForm.current_households" :min="0" style="width: 100%" />
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
const loading = ref(false)

const editingRow = ref(null)
const editForm = ref({
  income_target: 0,
  current_income: 0,
  households_target: 0,
  current_households: 0
})

const showBatchDialog = ref(false)
const batchForm = ref({
  group_id: null,
  income_target: 0,
  current_income: 0,
  households_target: 0,
  current_households: 0
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

const tableData = computed(() => {
  return groups.value.map(group => {
    const target = targets.value.find(t => t.group_id === group.id) || {}

    return {
      group_id: group.id,
      group_name: group.name,
      income_target: target.income_target || 0,
      households_target: target.households_target || 0,
      current_income: target.current_income || 0,
      current_households: target.current_households || 0,
      income_rate: target.income_completion_rate || 0,
      households_rate: target.households_completion_rate || 0
    }
  })
})

const startEdit = (row) => {
  editingRow.value = row.group_id
  editForm.value = {
    income_target: row.income_target,
    current_income: row.current_income,
    households_target: row.households_target,
    current_households: row.current_households
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
      current_income: editForm.value.current_income,
      households_target: editForm.value.households_target,
      current_households: editForm.value.current_households
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
    const groupsToUpdate = batchForm.value.group_id
      ? groups.value.filter(g => g.id === batchForm.value.group_id)
      : groups.value

    for (const group of groupsToUpdate) {
      await advisoryApi.saveTarget({
        group_id: group.id,
        year: selectedYear.value,
        income_target: batchForm.value.income_target,
        current_income: batchForm.value.current_income,
        households_target: batchForm.value.households_target,
        current_households: batchForm.value.current_households
      })
    }
    ElMessage.success('批量设置成功')
    showBatchDialog.value = false
    fetchTargets()
  } catch (error) {
    console.error('Batch save error:', error)
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
})

onMounted(() => {
  fetchGroups()
  fetchTargets()
  window.addEventListener('advisory-data-imported', fetchTargets)
})

onBeforeUnmount(() => {
  window.removeEventListener('advisory-data-imported', fetchTargets)
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
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16px;
}

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
  transition: all 0.15s ease;
  border: 1px solid transparent;
}

.table-body-row:hover {
  background: #F8FAFC;
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

.form-tip {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 4px;
}

:deep(.el-dialog__header) {
  font-weight: 600;
}

@media (max-width: 1100px) {
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
