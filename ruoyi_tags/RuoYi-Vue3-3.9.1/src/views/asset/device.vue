<template>
  <div class="app-container">
    <!-- 搜索和筛选区域 -->
    <el-card class="mb-4">
      <el-form :model="searchForm" label-width="100px" size="small">
        <el-row :gutter="20">
          <!-- 快速搜索 -->
          <el-col :span="8">
          <el-form-item label="快速搜索">
            <el-input v-model="searchForm.keyword" placeholder="设备名称/设备SN码" clearable>
              <template #append>
                <el-button type="primary" @click="handleSearch">搜索</el-button>
              </template>
            </el-input>
          </el-form-item>
        </el-col>
          <!-- 设备类型 -->
          <el-col :span="6">
            <el-form-item label="设备类型">
              <el-select v-model="searchForm.deviceType" multiple placeholder="选择设备类型" clearable>
                <el-option label="摄像头" value="camera" />
                <el-option label="门禁" value="access" />
                <el-option label="道闸" value="gate" />
                <el-option label="车牌识别" value="license" />
                <el-option label="红外探测器" value="infrared" />
                <el-option label="报警主机" value="alarm" />
              </el-select>
            </el-form-item>
          </el-col>
          <!-- 在线状态 -->
          <el-col :span="6">
            <el-form-item label="在线状态">
              <el-select v-model="searchForm.status" multiple placeholder="选择状态" clearable>
                <el-option label="正常" value="normal" />
                <el-option label="离线" value="offline" />
                <el-option label="报警" value="alarm" />
                <el-option label="故障" value="fault" />
              </el-select>
            </el-form-item>
          </el-col>
          <!-- 启用状态 -->
          <el-col :span="4">
            <el-form-item label="启用状态">
              <el-select v-model="searchForm.enabled" placeholder="选择状态" clearable>
                <el-option label="启用" value="1" />
                <el-option label="禁用" value="0" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <!-- 所属区域 -->
          <el-col :span="12">
            <el-form-item label="所属区域">
              <el-select v-model="searchForm.area" multiple placeholder="选择区域" clearable>
                <el-option label="园区" value="park" />
                <el-option label="楼栋" value="building" />
                <el-option label="楼层" value="floor" />
                <el-option label="具体区域" value="zone" />
              </el-select>
            </el-form-item>
          </el-col>
          <!-- 责任人 -->
          <el-col :span="12">
            <el-form-item label="责任人">
              <el-input v-model="searchForm.owner" placeholder="责任人姓名/工号" clearable />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 操作按钮区域 -->
    <el-card class="mb-4">
      <div class="flex justify-between items-center">
        <div>
          <el-button type="primary" @click="handleAdd">新增（补录）</el-button>
          <el-button @click="handleImport">批量导入</el-button>
          <el-button @click="handleExport">批量导出</el-button>
        </div>
        <div v-if="selectedRows.length > 0">
          <el-button @click="handleBatchEnable">批量启用</el-button>
          <el-button @click="handleBatchDisable">批量禁用</el-button>
          <el-button type="danger" @click="handleBatchDelete">批量删除</el-button>
        </div>
      </div>
    </el-card>

    <!-- 设备列表 -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="deviceList"
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="设备名称">
          <template #default="scope">
            <el-button type="text" @click="showDeviceDetail(scope.row)">{{ scope.row.name }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="sn" label="SN码" />
        <el-table-column prop="type" label="设备类型">
          <template #default="scope">
            <el-tag v-if="scope.row.type === 'camera'">摄像头</el-tag>
            <el-tag v-else-if="scope.row.type === 'access'">门禁</el-tag>
            <el-tag v-else-if="scope.row.type === 'gate'">道闸</el-tag>
            <el-tag v-else-if="scope.row.type === 'license'">车牌识别</el-tag>
            <el-tag v-else-if="scope.row.type === 'infrared'">红外探测器</el-tag>
            <el-tag v-else-if="scope.row.type === 'alarm'">报警主机</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="在线状态" width="150">
          <template #default="scope">
            <el-tooltip :content="getStatusText(scope.row.status)" placement="top">
              <el-tag 
                :type="getStatusType(scope.row.status)" 
                v-if="scope.row.status !== 'normal'"
                @click="viewAlarm(scope.row)"
                class="clickable-tag"
              >
                {{ getStatusText(scope.row.status).split('：')[0] }}
              </el-tag>
              <el-tag type="success" v-else>在线</el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="启用状态">
          <template #default="scope">
            <el-switch 
              v-model="scope.row.enabled" 
              active-value="1" 
              inactive-value="0"
              @change="handleEnableChange(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="责任人" />
        <el-table-column prop="area" label="所属区域" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-dropdown>
              <el-button type="primary" size="small">
                详情 <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleRemoteControl(scope.row)">远程控制</el-dropdown-item>
                  <el-dropdown-item @click="handleVideoPlayback(scope.row)">录像回放</el-dropdown-item>
                  <el-dropdown-item @click="handlePointBinding(scope.row)">点位绑定</el-dropdown-item>
                  <el-dropdown-item @click="handleEdit(scope.row)">编辑</el-dropdown-item>
                  <el-dropdown-item 
                    @click="handleEnableDisable(scope.row)"
                    :type="scope.row.enabled === '1' ? 'danger' : 'success'"
                  >
                    {{ scope.row.enabled === '1' ? '禁用' : '启用' }}
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleDelete(scope.row)" type="danger">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 设备详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="设备详情" width="600px">
      <el-form :model="currentDevice" label-width="120px">
        <el-form-item label="设备名称">
          <el-input v-model="currentDevice.name" disabled />
        </el-form-item>
        <el-form-item label="设备SN码">
          <el-input v-model="currentDevice.sn" disabled />
        </el-form-item>
        <el-form-item label="设备类型">
          <el-input :value="getDeviceTypeText(currentDevice.type)" disabled />
        </el-form-item>
        <el-form-item label="在线状态">
          <el-input :value="getStatusText(currentDevice.status)" disabled />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-input :value="currentDevice.enabled === '1' ? '启用' : '禁用'" disabled />
        </el-form-item>
        <el-form-item label="责任人">
          <el-input v-model="currentDevice.owner" disabled />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="currentDevice.phone" disabled />
        </el-form-item>
        <el-form-item label="所属区域">
          <el-input v-model="currentDevice.area" disabled />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="currentDevice.remark" type="textarea" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="viewFullDetail">查看完整详情</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="formDialogVisible" :title="isEdit ? '编辑设备' : '新增（补录）设备'" width="600px">
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="设备类型" prop="type">
          <el-select v-model="formData.type" placeholder="选择设备类型" disabled>
            <el-option label="摄像头" value="camera" />
            <el-option label="门禁" value="access" />
            <el-option label="道闸" value="gate" />
            <el-option label="车牌识别" value="license" />
            <el-option label="红外探测器" value="infrared" />
            <el-option label="报警主机" value="alarm" />
          </el-select>
        </el-form-item>
        <el-form-item label="设备SN码" prop="sn">
          <el-input v-model="formData.sn" disabled />
        </el-form-item>
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="formData.name" disabled />
        </el-form-item>
        <el-form-item label="责任人" prop="owner">
          <el-input v-model="formData.owner" placeholder="请输入责任人" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="所属区域" prop="area">
          <el-select v-model="formData.area" placeholder="选择所属区域">
            <el-option label="园区" value="park" />
            <el-option label="楼栋" value="building" />
            <el-option label="楼层" value="floor" />
            <el-option label="具体区域" value="zone" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="formData.remark" type="textarea" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="formDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 导入弹窗 -->
    <el-dialog v-model="importDialogVisible" title="批量导入" width="500px">
      <div class="import-container">
        <el-button type="primary" @click="downloadTemplate">下载标准模板</el-button>
        <el-upload
          class="upload-demo"
          action="#"
          :auto-upload="false"
          :on-change="handleFileChange"
          :file-list="fileList"
          accept=".xlsx,.xls"
        >
          <el-button type="primary">选择文件</el-button>
          <template #tip>
            <div class="el-upload__tip">
              请上传Excel格式文件，支持.xlsx和.xls格式
            </div>
          </template>
        </el-upload>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitImport">开始导入</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="DeviceLedger">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const selectedRows = ref([])
const searchForm = reactive({
  keyword: '',
  deviceType: [],
  status: [],
  enabled: '',
  area: [],
  owner: ''
})
const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

// 弹窗控制
const detailDialogVisible = ref(false)
const formDialogVisible = ref(false)
const importDialogVisible = ref(false)
const isEdit = ref(false)

// 数据
const currentDevice = reactive({})
const formData = reactive({})
const fileList = ref([])

// 表单验证规则
const formRules = reactive({
  owner: [{ required: true, message: '请填写责任人', trigger: 'blur' }],
  phone: [
    { required: true, message: '请填写联系电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  area: [{ required: true, message: '请选择所属区域', trigger: 'change' }]
})

// 模拟设备数据
const deviceList = ref([
  {
    id: 1,
    name: '园区大门摄像头',
    sn: 'CAM-20240101-001',
    type: 'camera',
    status: 'normal',
    enabled: '1',
    owner: '张三',
    phone: '13800138001',
    area: '园区',
    remark: '主入口摄像头'
  },
  {
    id: 2,
    name: '1号楼门禁',
    sn: 'ACC-20240101-001',
    type: 'access',
    status: 'offline',
    enabled: '1',
    owner: '李四',
    phone: '13900139001',
    area: '楼栋',
    remark: '1号楼入口门禁'
  },
  {
    id: 3,
    name: '地下车库道闸',
    sn: 'GATE-20240101-001',
    type: 'gate',
    status: 'normal',
    enabled: '0',
    owner: '王五',
    phone: '13700137001',
    area: '园区',
    remark: '地下车库入口道闸'
  }
])

// 计算属性
pagination.total = deviceList.value.length

// 方法
const handleSearch = () => {
  // 搜索逻辑
  ElMessage.success('搜索功能已触发')
}

const resetSearch = () => {
  Object.keys(searchForm).forEach(key => {
    searchForm[key] = Array.isArray(searchForm[key]) ? [] : ''
  })
}

const handleSelectionChange = (val) => {
  selectedRows.value = val
}

const handleSizeChange = (size) => {
  pagination.size = size
}

const handleCurrentChange = (current) => {
  pagination.current = current
}

const showDeviceDetail = (row) => {
  Object.assign(currentDevice, row)
  detailDialogVisible.value = true
}

const viewFullDetail = () => {
  router.push('/asset/device-detail')
  detailDialogVisible.value = false
}

const viewAlarm = (row) => {
  ElMessage.info('跳转到告警中心查看关联告警')
}

const getStatusType = (status) => {
  switch (status) {
    case 'normal': return 'success'
    case 'offline': return 'warning'
    case 'alarm': return 'danger'
    case 'fault': return 'info'
    default: return ''
  }
}

const getStatusColor = (status) => {
  switch (status) {
    case 'offline': return '#e6a23c'
    case 'alarm': return '#f56c6c'
    case 'fault': return '#909399'
    default: return '#67c23a'
  }
}

const getStatusIcon = (status) => {
  switch (status) {
    case 'normal': return 'CircleCheck'
    case 'offline': return 'Odometer'
    case 'alarm': return 'Warning'
    case 'fault': return 'Close'
    default: return 'CircleCheck'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'normal': return '正常：设备运行正常，无异常事件'
    case 'offline': return '离线：设备网络连接断开'
    case 'alarm': return '报警：设备触发告警事件'
    case 'fault': return '故障：设备运行异常'
    default: return ''
  }
}

const getDeviceTypeText = (type) => {
  switch (type) {
    case 'camera': return '摄像头'
    case 'access': return '门禁'
    case 'gate': return '道闸'
    case 'license': return '车牌识别'
    case 'infrared': return '红外探测器'
    case 'alarm': return '报警主机'
    default: return ''
  }
}

const handleAdd = () => {
  isEdit.value = false
  Object.assign(formData, {
    type: 'camera',
    sn: 'NEW-' + Date.now(),
    name: '新设备',
    owner: '',
    phone: '',
    area: '',
    remark: ''
  })
  formDialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(formData, row)
  formDialogVisible.value = true
}

const handleSubmit = () => {
  // 表单验证
  ElMessage.success(isEdit.value ? '编辑成功' : '新增成功')
  formDialogVisible.value = false
}

const handleEnableChange = (row) => {
  ElMessageBox.confirm(
    row.enabled === '1' ? '确认启用该设备？启用后设备将参与监控与告警' : '确认禁用该设备？禁用后设备将停止监控与告警',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success(row.enabled === '1' ? '启用成功' : '禁用成功')
  }).catch(() => {
    row.enabled = row.enabled === '1' ? '0' : '1'
  })
}

const handleEnableDisable = (row) => {
  handleEnableChange(row)
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    '删除后设备信息不可恢复，是否确认删除？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'danger'
    }
  ).then(() => {
    const index = deviceList.value.findIndex(item => item.id === row.id)
    if (index !== -1) {
      deviceList.value.splice(index, 1)
      pagination.total = deviceList.value.length
      ElMessage.success('删除成功')
    }
  })
}

const handleBatchEnable = () => {
  ElMessageBox.confirm('确认批量启用选中设备？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    selectedRows.value.forEach(row => {
      row.enabled = '1'
    })
    ElMessage.success('批量启用成功')
  })
}

const handleBatchDisable = () => {
  ElMessageBox.confirm('确认批量禁用选中设备？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    selectedRows.value.forEach(row => {
      row.enabled = '0'
    })
    ElMessage.success('批量禁用成功')
  })
}

const handleBatchDelete = () => {
  ElMessageBox.confirm('删除后设备信息不可恢复，是否确认批量删除？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'danger'
  }).then(() => {
    selectedRows.value.forEach(row => {
      const index = deviceList.value.findIndex(item => item.id === row.id)
      if (index !== -1) {
        deviceList.value.splice(index, 1)
      }
    })
    pagination.total = deviceList.value.length
    selectedRows.value = []
    ElMessage.success('批量删除成功')
  })
}

const handleImport = () => {
  importDialogVisible.value = true
}

const handleExport = () => {
  ElMessage.success('导出成功，文件已下载')
}

const downloadTemplate = () => {
  ElMessage.success('模板下载成功')
}

const handleFileChange = (file) => {
  fileList.value = [file]
}

const submitImport = () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }
  ElMessage.success('导入成功，共导入3条数据，0条失败')
  importDialogVisible.value = false
  fileList.value = []
}

const handleRemoteControl = (row) => {
  ElMessage.info('跳转到远程控制页面')
}

const handleVideoPlayback = (row) => {
  ElMessage.info('跳转到录像回放页面')
}

const handlePointBinding = (row) => {
  ElMessage.info('跳转到点位绑定页面')
}
</script>

<style scoped>
.app-container {
  padding: 20px;
}

.mb-4 {
  margin-bottom: 16px;
}

.flex {
  display: flex;
}

.justify-between {
  justify-content: space-between;
}

.items-center {
  align-items: center;
}

.clickable-tag {
  text-decoration: underline;
  cursor: pointer;
}
.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.import-container {
  padding: 20px 0;
}

.upload-demo {
  margin-top: 20px;
}

.dialog-footer {
  text-align: right;
}
</style>
