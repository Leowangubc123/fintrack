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
                <span class="leader-badge" :class="{ 'has-leader': group.leader }">
                  <el-icon :size="12"><User /></el-icon>
                  {{ group.leader || '未设专员' }}
                </span>
                <span class="member-count">成员 {{ group.member_count || 0 }}人</span>
              </div>
            </div>
            <div class="group-actions" @click.stop>
              <el-dropdown trigger="click">
                <el-icon :size="16" class="more-icon"><More /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="openGroupDialog(group)">
                      <el-icon><Edit /></el-icon>编辑营业部
                    </el-dropdown-item>
                    <el-dropdown-item @click="openLeaderDialog(group)">
                      <el-icon><User /></el-icon>任命专员
                    </el-dropdown-item>
                    <el-dropdown-item divided @click="deleteGroup(group)" class="delete-item">
                      <el-icon><Delete /></el-icon>删除营业部
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
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
          <div class="header-title-section">
            <span class="group-title">{{ selectedGroup.name }}</span>
            <span class="group-subtitle">
              <span class="leader-tag" :class="{ 'has-leader': selectedGroup.leader }">
                <el-icon :size="14"><User /></el-icon>
                {{ selectedGroup.leader || '未设专员' }}
              </span>
              <span class="divider">|</span>
              <span>成员 {{ selectedGroupMembers.length }}人</span>
            </span>
          </div>
          <div class="header-actions">
            <el-button type="primary" link @click="openLeaderDialog(selectedGroup)">
              <el-icon><User /></el-icon>任命专员
            </el-button>
            <button class="btn btn-primary" @click="openMemberDialog()">+ 添加成员</button>
          </div>
        </div>

        <div class="card-body">
          <table class="member-table">
            <thead>
              <tr>
                <th>姓名</th>
                <th>手机号</th>
                <th>功能范围</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="member in selectedGroupMembers" :key="member.id">
                <td>
                  <div class="member-name">
                    <div class="avatar-wrapper">
                      <div class="member-avatar">{{ member.name.charAt(0) }}</div>
                      <div v-if="selectedGroup.leader === member.name" class="leader-crown">
                        <el-icon :size="10"><User /></el-icon>
                      </div>
                    </div>
                    <div class="member-info">
                      <span class="name-text" :class="{ 'is-leader': selectedGroup.leader === member.name }">{{ member.name }}</span>
                      <span v-if="selectedGroup.leader === member.name" class="leader-label">专员</span>
                    </div>
                  </div>
                </td>
                <td>{{ member.phone ? maskPhone(member.phone) : '-' }}</td>
                <td>
                  <div class="scope-tags">
                    <span v-if="member.scope && member.scope.includes('public_fund')" class="scope-tag">公募</span>
                    <span v-if="member.scope && member.scope.includes('private_fund')" class="scope-tag">私募</span>
                    <span v-if="member.scope && member.scope.includes('advisory')" class="scope-tag">投顾</span>
                    <span v-if="member.scope && member.scope.includes('margin_trading')" class="scope-tag">两融</span>
                  </div>
                </td>
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
        <el-form-item label="功能范围">
          <el-checkbox-group v-model="memberForm.scopeList">
            <el-checkbox label="public_fund">公募产品</el-checkbox>
            <el-checkbox label="private_fund">私募产品</el-checkbox>
            <el-checkbox label="advisory">投资顾问</el-checkbox>
            <el-checkbox label="margin_trading">两融数据</el-checkbox>
          </el-checkbox-group>
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

    <!-- 任命专员弹窗 -->
    <el-dialog
      v-model="showLeaderDialog"
      title="任命营业部专员"
      width="400px"
    >
      <p style="margin-bottom: 16px;">
        为 <strong>{{ editingGroup?.name }}</strong> 任命专员:
      </p>
      <el-select
        v-model="leaderForm.leader"
        placeholder="请选择或输入专员姓名"
        style="width: 100%;"
        filterable
        allow-create
        default-first-option
      >
        <el-option
          v-for="member in editingGroupMembers"
          :key="member.id"
          :label="member.name"
          :value="member.name"
        />
      </el-select>
      <p style="margin-top: 12px; color: #6E6E73; font-size: 13px;">
        提示: 可以直接输入姓名任命，或从当前营业部成员中选择
      </p>
      <template #footer>
        <el-button @click="showLeaderDialog = false">取消</el-button>
        <el-button type="primary" @click="saveLeader">确认任命</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { groupsApi, membersApi } from '../api'
import { OfficeBuilding, Folder, InfoFilled, More, Edit, User, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const groups = ref([])
const selectedGroup = ref(null)
const selectedGroupMembers = ref([])

// 弹窗状态
const showGroupDialog = ref(false)
const showMemberDialog = ref(false)
const showTransferDialog = ref(false)
const showLeaderDialog = ref(false)
const editingGroup = ref(null)
const editingMember = ref(null)
const transferringMember = ref(null)
const targetGroupId = ref('')
const editingGroupMembers = ref([])

// 表单
const groupForm = ref({ name: '', leader: '', region: '', remark: '' })
const memberForm = ref({ name: '', phone: '', scopeList: ['public_fund', 'private_fund', 'advisory', 'margin_trading'] })
const leaderForm = ref({ leader: '' })
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
    const scopeList = member.scope ? member.scope.split(',') : ['public_fund', 'private_fund', 'advisory', 'margin_trading']
    memberForm.value = { name: member.name, phone: member.phone, scopeList }
  } else {
    memberForm.value = { name: '', phone: '', scopeList: ['public_fund', 'private_fund', 'advisory', 'margin_trading'] }
  }
  showMemberDialog.value = true
}

async function saveMember() {
  await memberFormRef.value.validate()
  try {
    const scope = memberForm.value.scopeList.join(',')
    const payload = {
      name: memberForm.value.name,
      phone: memberForm.value.phone,
      scope
    }
    if (editingMember.value) {
      await membersApi.update(editingMember.value.id, payload)
      ElMessage.success('更新成功')
    } else {
      await membersApi.create({ ...payload, group_id: selectedGroup.value.id })
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

// 打开任命专员弹窗
async function openLeaderDialog(group) {
  editingGroup.value = group
  leaderForm.value = { leader: group.leader || '' }

  // 获取该营业部的成员列表
  try {
    const res = await membersApi.list(group.id)
    editingGroupMembers.value = res
  } catch (error) {
    editingGroupMembers.value = []
  }

  showLeaderDialog.value = true
}

// 保存专员任命
async function saveLeader() {
  if (!editingGroup.value) return

  try {
    await groupsApi.update(editingGroup.value.id, {
      name: editingGroup.value.name,
      leader: leaderForm.value.leader
    })
    ElMessage.success('专员任命成功')
    showLeaderDialog.value = false
    loadGroups()
  } catch (error) {
    ElMessage.error('任命失败')
  }
}

// 删除营业部
async function deleteGroup(group) {
  try {
    await ElMessageBox.confirm(
      `确定删除营业部 "${group.name}" 吗？\n删除后该营业部的成员将被清空，相关销售数据将保留但不再关联营业部。`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消'
      }
    )

    await groupsApi.delete(group.id)
    ElMessage.success('营业部已删除')

    // 如果删除的是当前选中的营业部，清空选择
    if (selectedGroup.value?.id === group.id) {
      selectedGroup.value = null
      selectedGroupMembers.value = []
    }

    loadGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
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

.header-title-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
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
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.leader-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  background: #F5F5F7;
  color: #8E8E93;
  border: 1px solid transparent;
}

.leader-badge.has-leader {
  background: linear-gradient(135deg, #E3F5E8, #D1F2D9);
  color: #059669;
  border-color: #34C759;
}

.member-count {
  font-size: 11px;
  color: #6E6E73;
}

.group-actions {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.group-card:hover .group-actions {
  opacity: 1;
}

.more-icon {
  color: #6E6E73;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.more-icon:hover {
  background: #E5E5EA;
  color: #1D1D1F;
}

.delete-item {
  color: #FF3B30;
}

.delete-item:hover {
  color: #FF3B30;
  background: #FFE5E3;
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
  display: flex;
  align-items: center;
  gap: 12px;
}

.leader-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  background: #F5F5F7;
  color: #8E8E93;
  border: 1px solid transparent;
}

.leader-tag.has-leader {
  background: linear-gradient(135deg, #E3F5E8, #D1F2D9);
  color: #059669;
  border-color: #34C759;
}

.divider {
  color: #D1D5DB;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
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

.member-name {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar-wrapper {
  position: relative;
  display: inline-flex;
}

.member-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #007AFF, #5856D6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.leader-crown {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 16px;
  height: 16px;
  background: #34C759;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  border: 2px solid white;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-text {
  font-size: 14px;
  color: #1D1D1F;
  font-weight: 500;
}

.name-text.is-leader {
  font-weight: 600;
}

.leader-label {
  font-size: 11px;
  font-weight: 600;
  color: #059669;
  background: #E3F5E8;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #34C759;
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

.scope-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.scope-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: #F3F4F6;
  color: #6B7280;
}

.scope-tag:nth-child(1) {
  background: #DBEAFE;
  color: #1D4ED8;
}

.scope-tag:nth-child(2) {
  background: #EDE9FE;
  color: #7C3AED;
}

.scope-tag:nth-child(3) {
  background: #CCFBF1;
  color: #0F766E;
}

.scope-tag:nth-child(4) {
  background: #FFF7ED;
  color: #EA580C;
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
