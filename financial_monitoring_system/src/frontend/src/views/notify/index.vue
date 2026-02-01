<template>
  <div class="notify-page">
    <!-- 操作栏 -->
    <el-card class="action-card">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新增渠道
      </el-button>
      <el-button @click="loadChannels">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </el-card>
    
    <!-- 渠道列表 -->
    <el-card>
      <el-table :data="channelsList" stripe style="width: 100%">
        <el-table-column prop="name" label="名称" width="180" />
        <el-table-column prop="code" label="编码" width="150" />
        <el-table-column prop="channel_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getTypeText(row.channel_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
              {{ row.status === 'active' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleTest(row)">测试</el-button>
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑渠道' : '新增渠道'" 
      width="600px"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="formData.code" :disabled="isEdit" placeholder="英文唯一标识" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="渠道名称" />
        </el-form-item>
        <el-form-item label="类型" prop="channel_type">
          <el-select v-model="formData.channel_type" placeholder="选择类型" @change="handleTypeChange">
            <el-option v-for="t in channelTypes" :key="t.code" :label="`${t.name} - ${t.description}`" :value="t.code" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="配置信息" prop="config">
          <el-input 
            v-model="configJson" 
            type="textarea" 
            :rows="4" 
            placeholder="JSON格式的配置"
          />
          <div v-if="currentTypeConfig" class="config-tip">
            需要字段: {{ currentTypeConfig.config_fields?.join(', ') }}
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { notifyApi } from '@/api'

const channelsList = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const channelTypes = ref([])
const currentTypeConfig = ref(null)

const formData = reactive({
  id: null,
  code: '',
  name: '',
  channel_type: '',
  config: {},
  status: 'active'
})

const configJson = ref('{}')

const rules = {
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  channel_type: [{ required: true, message: '请选择类型', trigger: 'change' }]
}

const loadChannels = async () => {
  try {
    const res = await notifyApi.getList()
    channelsList.value = res.channels || []
  } catch (e) {
    ElMessage.error('加载渠道失败')
  }
}

const loadChannelTypes = async () => {
  try {
    const res = await notifyApi.getTypes()
    channelTypes.value = res.types || []
  } catch (e) {
    console.error('加载类型失败:', e)
  }
}

const handleCreate = () => {
  isEdit.value = false
  formData.id = null
  formData.code = ''
  formData.name = ''
  formData.channel_type = ''
  formData.config = {}
  formData.status = 'active'
  configJson.value = '{}'
  currentTypeConfig.value = null
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(formData, row)
  formData.id = row.id
  configJson.value = JSON.stringify(row.config || {}, null, 2)
  
  currentTypeConfig.value = channelTypes.value.find(t => t.code === row.channel_type)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    try {
      formData.config = JSON.parse(configJson.value)
    } catch (e) {
      ElMessage.error('配置信息必须是有效的JSON格式')
      return
    }
    
    if (isEdit.value) {
      await notifyApi.update(formData.id, formData)
      ElMessage.success('更新成功')
    } else {
      await notifyApi.create(formData)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadChannels()
  } catch (e) {
    if (e !== false) {
      ElMessage.error('操作失败')
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该渠道吗?', '提示', { type: 'warning' })
    await notifyApi.delete(row.id)
    ElMessage.success('删除成功')
    loadChannels()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleTest = async (row) => {
  try {
    const res = await notifyApi.test(row.id)
    if (res.success) {
      ElMessage.success('测试消息已发送')
    } else {
      ElMessage.warning('发送失败: ' + res.message)
    }
  } catch (e) {
    ElMessage.error('测试失败')
  }
}

const handleTypeChange = (value) => {
  currentTypeConfig.value = channelTypes.value.find(t => t.code === value)
  // 设置默认配置模板
  const templates = {
    lark: { webhook_url: '' },
    wecom: { key: '' },
    email: { smtp_host: '', smtp_port: 25, username: '', password: '', from_address: '' },
    dingtalk: { access_token: '', secret: '' },
    telegram: { bot_token: '', chat_id: '' },
    webhook: { url: '', method: 'POST' }
  }
  formData.config = templates[value] || {}
  configJson.value = JSON.stringify(formData.config, null, 2)
}

const getTypeText = (type) => {
  const texts = {
    lark: '飞书',
    wecom: '企业微信',
    email: '邮件',
    dingtalk: '钉钉',
    telegram: 'Telegram',
    webhook: 'Webhook'
  }
  return texts[type] || type
}

onMounted(() => {
  loadChannels()
  loadChannelTypes()
})
</script>

<style lang="scss" scoped>
.notify-page {
  .action-card {
    margin-bottom: 20px;
  }
  
  .config-tip {
    font-size: 12px;
    color: #999;
    margin-top: 4px;
  }
}
</style>
