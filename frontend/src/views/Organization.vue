<template>
  <div class="organization-page">
    <div class="org-layout">
      <!-- 左侧营业部卡片 -->
      <div class="group-list-card">
        <div class="card-header">
          <div class="card-title">
            <el-icon :size="20"><OfficeBuilding /></el-icon>
            营业部列表
          </div>
          <button class="btn btn-primary" @click="openGroupDialog()">+ 新建</button>
        </div>

        <div class="group-cards" v-loading="loading">
          <div
            v-for="group in groups"
            :key="group.id"
            class="group-card"
            :class="{ active: selectedGroup?.id === group.id }"
            @click="selectGroup(group)"
          >
            <div class="group-icon">
              <el-icon :size="20"><Folder /></el-icon>
            </div>
            <div class="group-info">
              <div class="group-name">{{ group.name }}</div>
              <div class="group-meta">
                专员: {{ group.leader || '未设置' }} | 成员: {{ group.member_count || 0 }}人
              </div>
            </div>
          </div>

          <el-empty v-if="groups.length === 0" description="暂无营业部" />
        </div>

        <div class="group-summary" v-if="groups.length > 0">
          共 {{ groups.length }} 个营业部 | {{ totalMembers }} 人
        </div>
      </div>

      <!-- 右侧成员列表 -->
      <div class="card" v-if="selectedGroup">
        <div class="card-header">
          <div>
            <span class="group-title">{{ selectedGroup.name }}</span>
            <span class="group-subtitle">
              专员: {{ selectedGroup.leader || '未设置' }} | 成员: {{ selectedGroupMembers.length }}人
            </span>
          </div>
          <button class="btn btn-primary" @click="openMemberDialog()">+ 添加成员</button>
        </div>

        <div class="card-body">
          <table class="member-table">
            <thead>
              <tr>
                <th>姓名</th>
                <th>手机号</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="member in selectedGroupMembers" :key="member.id">
                <td>
                  <div class="member-name">
                    <div class="member-avatar">{{ member.name.charAt(0) }}</div>
                    <span>{{ member.name }}</span>
                  </div>
                </td>
                <td>{{ member.phone ? maskPhone(member.phone) : '-' }}</td>
                <td>
                  <div class="member-actions">
                    <span class="action-link" @click="editMember(member)">编辑</span>
                    <span class="action-link" @click="openTransferDialog(member)">转组</span>
                    <span class="action-link delete" @click="deleteMember(member)">删除</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <div class="member-tips">
            <el-icon :size="14"><InfoFilled /></el-icon>
            提示: 成员转组后，历史销售数据仍归属于原营业部
          </div>
        </div>
      </div>

      <div class="card empty-card" v-else>
        <el-empty description="请选择营业部" />
      </div>
    </div>

    <!-- 新建/编辑营业部弹窗 -->
    <el-dialog
      v-model="showGroupDialog"
      :title="editingGroup ? '编辑营业部' : '新建营业部'"
      width="400px"
    >
      <el-form :model="groupForm" label-width="90px" :rules="groupRules" ref="groupFormRef">
        <el-form-item label="营业部名称" prop="name">
          <el-input v-model="groupForm.name" placeholder="请输入营业部名称" />
        </el-form-item>
        <el-form-item label="产品专员">
          <el-input v-model="groupForm.leader" placeholder="请输入专员姓名" />
        </el-form-item>
        <el-form-item label="所属区域">
          <el-input v-model="groupForm.region" placeholder="请输入所属区域" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="groupForm.remark" type="textarea" :rows="3" placeholder="请输入备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGroupDialog = false">取消</el-button>
        <el-button type="primary" @click="saveGroup">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑成员弹窗 -->
    <el-dialog
      v-model="showMemberDialog"
      :title="editingMember ? '编辑成员' : '添加成员'"
      width="400px"
    >
      <el-form :model="memberForm" label-width="80px" :rules="memberRules" ref="memberFormRef">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="memberForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="memberForm.phone" placeholder="请输入手机号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showMemberDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMember">保存</el-button>
      </template>
    </el-dialog>

    <!-- 转组弹窗 -->
    <el-dialog
      v-model="showTransferDialog"
      title="成员转组"
      width="400px"
    >
      <p style="margin-bottom: 16px;">
        将 <strong>{{ transferringMember?.name }}</strong> 转至:
      </p>
      <el-select v-model="targetGroupId" placeholder="请选择目标营业部" style="width: 100%;">
        <el-option
          v-for="group in groups.filter(g => g.id !== selectedGroup?.id)"
          :key="group.id"
          :label="group.name"
          :value="group.id"
        />
      </el-select>
      <template #footer>
        <el-button @click="showTransferDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmTransfer">确认转组</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { groupsApi, membersApi } from '../api'
import { OfficeBuilding, Folder, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const groups = ref([])
const selectedGroup = ref(null)
const selectedGroupMembers = ref([])

// 弹窗状态
const showGroupDialog = ref(false)
const showMemberDialog = ref(false)
const showTransferDialog = ref(false)
const editingGroup = ref(null)
const editingMember = ref(null)
const transferringMember = ref(null)
const targetGroupId = ref('')

// 表单
const groupForm = ref({ name: '', leader: '', region: '', remark: '' })
const memberForm = ref({ name: '', phone: '' })
const groupFormRef = ref()
const memberFormRef = ref()

const groupRules = {
  name: [{ required: true, message: '请输入营业部名称', trigger: 'blur' }]
}

const memberRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }]
}

const totalMembers = computed(() => {
  return groups.value.reduce((sum, g) => sum + (g.member_count || 0), 0)
})

onMounted(() => {
  loadGroups()
})

async function loadGroups() {
  loading.value = true
  try {
    const res = await groupsApi.list()
    groups.value = res
    if (res.length > 0 && !selectedGroup.value) {
      selectGroup(res[0])
    }
  } catch (error) {
    ElMessage.error('加载营业部失败')
  } finally {
    loading.value = false
  }
}

async function selectGroup(group) {
  selectedGroup.value = group
  try {
    const res = await membersApi.list(group.id)
    selectedGroupMembers.value = res
  } catch (error) {
    ElMessage.error('加载成员失败')
  }
}

function openGroupDialog(group = null) {
  editingGroup.value = group
  if (group) {
    groupForm.value = { ...group }
  } else {
    groupForm.value = { name: '', leader: '', region: '', remark: '' }
  }
  showGroupDialog.value = true
}

async function saveGroup() {
  await groupFormRef.value.validate()
  try {
    if (editingGroup.value) {
      await groupsApi.update(editingGroup.value.id, groupForm.value)
      ElMessage.success('更新成功')
    } else {
      await groupsApi.create(groupForm.value)
      ElMessage.success('创建成功')
    }
    showGroupDialog.value = false
    loadGroups()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

function openMemberDialog(member = null) {
  editingMember.value = member
  if (member) {
    memberForm.value = { name: member.name, phone: member.phone }
  } else {
    memberForm.value = { name: '', phone: '' }
  }
  showMemberDialog.value = true
}

async function saveMember() {
  await memberFormRef.value.validate()
  try {
    if (editingMember.value) {
      await membersApi.update(editingMember.value.id, memberForm.value)
      ElMessage.success('更新成功')
    } else {
      await membersApi.create({ ...memberForm.value, group_id: selectedGroup.value.id })
      ElMessage.success('添加成功')
    }
    showMemberDialog.value = false
    selectGroup(selectedGroup.value)
    loadGroups()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

function editMember(member) {
  openMemberDialog(member)
}

async function deleteMember(member) {
  try {
    await ElMessageBox.confirm('确定删除该成员吗？', '提示', { type: 'warning' })
    await membersApi.delete(member.id)
    ElMessage.success('删除成功')
    selectGroup(selectedGroup.value)
    loadGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

function openTransferDialog(member) {
  transferringMember.value = member
  targetGroupId.value = ''
  showTransferDialog.value = true
}

async function confirmTransfer() {
  if (!targetGroupId.value) {
    ElMessage.warning('请选择目标营业部')
    return
  }
  try {
    await membersApi.transfer(transferringMember.value.id, targetGroupId.value)
    ElMessage.success('转组成功')
    showTransferDialog.value = false
    selectGroup(selectedGroup.value)
    loadGroups()
  } catch (error) {
    ElMessage.error('转组失败')
  }
}

function maskPhone(phone) {
  if (!phone || phone.length < 7) return phone
  return phone.slice(0, 3) + '****' + phone.slice(-4)
}
</script>

<style scoped>
.organization-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* 营销人员 - 左右布局 */
.org-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 24px;
}

.group-list-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 140px);
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 17px;
  font-weight: 600;
  color: #1D1D1F;
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-cards {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.group-card {
  padding: 16px 20px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.group-card:hover {
  background: #F5F5F7;
}

.group-card.active {
  background: #F5F5F7;
  box-shadow: inset 3px 0 0 #007AFF;
}

.group-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #007AFF, #5856D6);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.group-info {
  flex: 1;
}

.group-name {
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 2px;
  font-size: 15px;
}

.group-meta {
  font-size: 12px;
  color: #6E6E73;
}

.group-summary {
  padding: 16px;
  text-align: center;
  color: #6E6E73;
  font-size: 13px;
  background: #FAFAFA;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.empty-card {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.card-body {
  padding: 24px;
}

.group-title {
  font-size: 18px;
  font-weight: 600;
  color: #1D1D1F;
  margin-right: 12px;
}

.group-subtitle {
  font-size: 13px;
  color: #6E6E73;
}

/* 按钮 */
.btn {
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.btn-primary {
  background: #007AFF;
  color: white;
}

.btn-primary:hover {
  background: #0056CC;
}

/* 成员列表 */
.member-table {
  width: 100%;
  border-collapse: collapse;
}

.member-table th,
.member-table td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.member-table th {
  background: #F5F5F7;
  font-weight: 600;
  color: #6E6E73;
  font-size: 13px;
}

.member-table tr:hover {
  background: #FAFAFA;
}

.member-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.member-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #007AFF, #5856D6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 13px;
  font-weight: 600;
}

.member-actions {
  display: flex;
  gap: 12px;
}

.action-link {
  color: #007AFF;
  font-size: 13px;
  cursor: pointer;
  font-weight: 500;
}

.action-link:hover {
  text-decoration: underline;
}

.action-link.delete {
  color: #FF3B30;
}

.member-tips {
  margin-top: 16px;
  padding: 12px 16px;
  background: #F0F9FF;
  border-radius: 10px;
  color: #007AFF;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
