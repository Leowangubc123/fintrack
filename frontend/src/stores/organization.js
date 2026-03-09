import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { groupsApi, membersApi } from '../api'

export const useOrganizationStore = defineStore('organization', () => {
  // State
  const groups = ref([])
  const members = ref([])
  const selectedGroup = ref(null)
  const loading = ref(false)

  // Getters
  const selectedGroupMembers = computed(() => {
    if (!selectedGroup.value) return []
    return members.value.filter(m => m.group_id === selectedGroup.value.id)
  })

  const totalMembers = computed(() => members.value.length)

  // Actions
  async function fetchGroups() {
    loading.value = true
    try {
      const res = await groupsApi.list()
      groups.value = res
      // 默认选中第一个
      if (groups.value.length > 0 && !selectedGroup.value) {
        selectedGroup.value = groups.value[0]
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchMembers() {
    try {
      const res = await membersApi.list()
      members.value = res
    } catch (error) {
      console.error('获取成员列表失败:', error)
    }
  }

  async function createGroup(data) {
    await groupsApi.create(data)
    await fetchGroups()
  }

  async function updateGroup(id, data) {
    await groupsApi.update(id, data)
    await fetchGroups()
  }

  async function deleteGroup(id) {
    await groupsApi.delete(id)
    await fetchGroups()
    if (selectedGroup.value?.id === id) {
      selectedGroup.value = groups.value[0] || null
    }
  }

  async function createMember(data) {
    await membersApi.create(data)
    await fetchMembers()
    await fetchGroups() // 更新成员数量
  }

  async function updateMember(id, data) {
    await membersApi.update(id, data)
    await fetchMembers()
    if (data.group_id) {
      await fetchGroups()
    }
  }

  async function deleteMember(id) {
    await membersApi.delete(id)
    await fetchMembers()
    await fetchGroups()
  }

  async function transferMember(id, targetGroupId) {
    await membersApi.transfer(id, targetGroupId)
    await fetchMembers()
    await fetchGroups()
  }

  return {
    groups,
    members,
    selectedGroup,
    loading,
    selectedGroupMembers,
    totalMembers,
    fetchGroups,
    fetchMembers,
    createGroup,
    updateGroup,
    deleteGroup,
    createMember,
    updateMember,
    deleteMember,
    transferMember
  }
})