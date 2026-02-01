<template>
  <div class="datasources-page">
    <!-- 操作栏 -->
    <el-card class="action-card">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新增数据源
      </el-button>
      <el-button @click="loadDatasources">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </el-card>
    
    <!-- 数据源列表 -->
    <el-card>
      <el-table :data="datasourcesList" stripe style="width: 100%">
        <el-table-column prop="name" label="名称" width="180" />
        <el-table-column prop="code" label="编码" width="150" />
        <el-table-column prop="source_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getTypeText(row.source_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
              {{ row.status === 'active' ? '正常' : '异常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sync_interval" label="同步间隔(秒)" width="120" />
        <el-table-column prop="last_sync_time" label="最后同步" width="180">
          <template #default="{ row }">
            {{ row.last_sync_time ? formatTime(row.last_sync_time) : '从未同步' }}
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleTest(row)">测试</el-button>
            <el-button type="primary" link @click="handleSync(row)">同步</el-button>
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑数据源' : '新增数据源'" 
      width="600px"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="编码" prop="code">
          <el-input v-model="formData.code" :disabled="isEdit" placeholder="英文唯一标识" />
        </el-form-item>
        <el-form-item label="类型" prop="source_type">
          <el-select v-model="formData.source_type" placeholder="请选择类型" @change="handleTypeChange">
            <el-option 
              v-for="type in sourceTypes" 
              :key="type.code" 
              :label="type.name" 
              :value="type.code" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="连接信息" prop="connection_info">
          <el-input 
            v-model="connectionInfoJson" 
            type="textarea" 
            :rows="4" 
            placeholder="JSON格式的连接配置"
          />
        </el-form-item>
        
        <el-form-item label="同步间隔">
          <el-input-number v-model="formData.sync_interval" :min="60" :step="60" />
          <span class="form-tip">秒</span>
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
import { datasourcesApi } from '@/api'

const datasourcesList = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const sourceTypes = ref([])

const formData = reactive({
  id: null,
  name: '',
  code: '',
  source_type: '',
  connection_info: {},
  sync_interval: 300
})

const connectionInfoJson = ref('')

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  source_type: [{ required: true, message: '请选择类型', trigger: 'change' }]
}

const loadDatasources = async () => {
  try {
    const res = await datasourcesApi.getList({ page: 1, page_size: 100 })
    datasourcesList.value = res.items || []
  } catch (e) {
    ElMessage.error('加载数据源失败')
  }
}

const loadSourceTypes = async () => {
  try {
    const res = await datasourcesApi.getTypes()
    sourceTypes.value = res.types || []
  } catch (e) {
    console.error('加载类型列表失败:', e)
  }
}

const handleCreate = () => {
  isEdit.value = false
  formData.id = null
  formData.name = ''
  formData.code = ''
  formData.source_type = ''
  formData.connection_info = {}
  formData.sync_interval = 300
  connectionInfoJson.value = '{}'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(formData, row)
  formData.id = row.id
  connectionInfoJson.value = JSON.stringify(row.connection_info || {}, null, 2)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    // 解析连接信息
    try {
      formData.connection_info = JSON.parse(connectionInfoJson.value)
    } catch (e) {
      ElMessage.error('连接信息必须是有效的JSON格式')
      return
    }
    
    if (isEdit.value) {
      await datasourcesApi.update(formData.id, formData)
      ElMessage.success('更新成功')
    } else {
      await datasourcesApi.create(formData)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadDatasources()
  } catch (e) {
    if (e !== false) {
      ElMessage.error('操作失败')
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该数据源吗?', '提示', { type: 'warning' })
    await datasourcesApi.delete(row.id)
    ElMessage.success('删除成功')
    loadDatasources()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleTest = async (row) => {
  try {
    const res = await datasourcesApi.test(row.id)
    if (res.success) {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.warning('连接测试失败: ' + res.message)
    }
  } catch (e) {
    ElMessage.error('测试失败')
  }
}

const handleSync = async (row) => {
  try {
    await datasourcesApi.sync(row.id)
    ElMessage.success('同步任务已启动')
    loadDatasources()
  } catch (e) {
    ElMessage.error('启动同步失败')
  }
}

const handleTypeChange = (value) => {
  // 根据类型设置默认连接信息模板
  const templates = {
    database_view: { path: '', view_name: '' },
    csv_file: { path: '' },
    excel_file: { path: '', sheet_name: 0 },
    json_file: { path: '' },
    xml_file: { path: '' },
    log_file: { path: '' }
  }
  formData.connection_info = templates[value] || {}
  connectionInfoJson.value = JSON.stringify(formData.connection_info, null, 2)
}

const getTypeText = (type) => {
  const texts = {
    database_view: '数据库视图',
    csv_file: 'CSV文件',
    excel_file: 'Excel文件',
    json_file: 'JSON文件',
    xml_file: 'XML文件',
    log_file: '日志文件'
  }
  return texts[type] || type
}

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadDatasources()
  loadSourceTypes()
})
</script>

<style lang="scss" scoped>
.datasources-page {
  .action-card {
    margin-bottom: 20px;
  }
  
  .form-tip {
    margin-left: 8px;
    color: #999;
  }
}
</style>
