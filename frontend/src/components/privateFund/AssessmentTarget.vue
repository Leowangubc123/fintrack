<template>
  <div class="assessment-target">
    <!-- Header -->
    <div class="view-header">
      <div class="header-title">营业部考核指标</div>
      <div class="header-actions">
        <el-select v-model="selectedYear" class="year-select">
          <el-option v-for="year in years" :key="year" :label="year + '年'" :value="year" />
        </el-select>
        <el-button type="primary" class="batch-btn" @click="showBatchDialog = true">
          <el-icon><Plus /></el-icon>批量设置指标
        </el-button>
      </div>
    </div>

    <!-- Targets Table -->
    <div class="targets-card">
      <div class="custom-table">
        <div class="table-head">
          <div class="th" style="width: 50px">序号</div>
          <div class="th" style="width: 140px">营业部</div>
          <div class="th" style="width: 120px" align="right">销量目标</div>
          <div class="th" style="width: 120px" align="right">当前考核销量</div>
          <div class="th" style="width: 140px" align="right">完成率</div>
          <div class="th" style="width: 100px" align="right">时间进度</div>
          <div class="th" style="width: 80px" align="center">状态</div>
          <div class="th" style="width: 100px" align="center">操作</div>
        </div>
        <div
          v-for="(row, index) in tableData"
          :key="row.group_id"
          class="table-body-row"
          :class="{ editing: editingRow === row.group_id }"
        >
          <div class="td" style="width: 50px" data-label="序号">{{ index + 1 }}</div>
          <div class="td" style="width: 140px" data-label="营业部">
            <span class="group-name">{{ row.group_name }}</span>
          </div>
          <div class="td" style="width: 120px" align="right" data-label="销量目标">
            <div v-if="editingRow === row.group_id" class="edit-field">
              <el-input-number v-model="editForm.sales_target" :min="0" :precision="2" size="small" style="width: 110px" />
            </div>
            <span v-else>{{ row.sales_target?.toFixed(2) || '0.00' }}万</span>
          </div>
          <div class="td" style="width: 120px" align="right" data-label="当前考核销量">{{ row.current_sales?.toFixed(2) || '0.00' }}万</div>
          <div class="td" style="width: 140px" align="right" data-label="完成率">
            <div class="rate-cell">
              <div class="rate-bar-bg">
                <div
                  class="rate-bar-fill"
                  :class="getProgressClass(row.completion_rate)"
                  :style="{ width: Math.min(row.completion_rate || 0, 100) + '%' }"
                />
              </div>
              <span class="rate-text" :class="getProgressClass(row.completion_rate)">
                {{ row.completion_rate || 0 }}%
              </span>
            </div>
          </div>
          <div class="td" style="width: 100px" align="right" data-label="时间进度">{{ row.time_progress }}%</div>
          <div class="td" style="width: 80px" align="center" data-label="状态">
            <el-tag :type="getStatusTagType(row.status)" size="small">{{ getStatusLabel(row.status) }}</el-tag>
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
      <el-form label-width="100px">
        <el-form-item label="营业部">
          <el-select v-model="batchForm.group_id" placeholder="选择营业部" style="width: 100%">
            <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
          <div class="form-tip">不选择则设置所有营业部</div>
        </el-form-item>
        <el-form-item label="销量目标">
          <el-input-number v-model="batchForm.sales_target" :min="0" :precision="2" style="width: 100%" />
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
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { privateFundApi } from '../../api/index.js'
import { groupsApi } from '../../api/index.js'

const selectedYear = ref(new Date().getFullYear())
const years = computed(() => {
  const current = new Date().getFullYear()
  return [current, current + 1]
})

const groups = ref([])
const targets = ref([])

const editingRow = ref(null)
const editForm = ref({
  sales_target: 0
})

const showBatchDialog = ref(false)
const batchForm = ref({
  group_id: null,
  sales_target: 0
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
  try {
    const res = await privateFundApi.getTargets(selectedYear.value)
    targets.value = res || []
  } catch (error) {
    console.error('Failed to fetch targets:', error)
    ElMessage.error('获取考核数据失败')
  }
}

const tableData = computed(() => {
  return targets.value.sort((a, b) => b.current_sales - a.current_sales)
})

const startEdit = (row) => {
  editingRow.value = row.group_id
  editForm.value = {
    sales_target: row.sales_target
  }
}

const cancelEdit = () => {
  editingRow.value = null
}

const saveEdit = async (row) => {
  try {
    await privateFundApi.saveTarget({
      group_id: row.group_id,
      year: selectedYear.value,
      sales_target: editForm.value.sales_target
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
      await privateFundApi.saveTarget({
        group_id: batchForm.value.group_id,
        year: selectedYear.value,
        sales_target: batchForm.value.sales_target
      })
    } else {
      for (const group of groups.value) {
        await privateFundApi.saveTarget({
          group_id: group.id,
          year: selectedYear.value,
          sales_target: batchForm.value.sales_target
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

const getProgressClass = (rate) => {
  if (rate >= 100) return 'success'
  if (rate >= 50) return 'warning'
  return 'danger'
}

const getStatusTagType = (status) => {
  if (status === 'ahead') return 'success'
  if (status === 'behind') return 'danger'
  return 'info'
}

const getStatusLabel = (status) => {
  if (status === 'ahead') return '超前'
  if (status === 'behind') return '落后'
  return '正常'
}

watch(selectedYear, () => {
  fetchTargets()
})

onMounted(() => {
  fetchGroups()
  fetchTargets()
})
</script>

<style scoped>
.assessment-target {
  padding: 0;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: white;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.year-select {
  width: 110px;
}

.batch-btn {
  font-weight: 500;
}

.targets-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
  padding: 20px 24px;
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

@media (max-width: 900px) {
  .view-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

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
