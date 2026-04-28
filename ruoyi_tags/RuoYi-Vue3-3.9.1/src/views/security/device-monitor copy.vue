<template>
  <div class="app-container">
    <!-- 搜索和筛选区域 -->
    <el-card class="mb-4">
      <el-form :model="searchForm" label-width="100px" size="small">
        <el-row :gutter="20">
          <!-- 快速搜索 -->
          <el-col :span="8">
            <el-form-item label="快速搜索">
              <el-input v-model="searchForm.keyword" placeholder="设备名称/设备SN码/所属区域" clearable>
                <template #append>
                  <el-button type="primary" @click="handleSearch">搜索</el-button>
                  <el-button @click="resetSearch">重置</el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          <!-- 设备状态 -->
          <el-col :span="6">
            <el-form-item label="设备状态">
              <el-select v-model="searchForm.status" multiple placeholder="选择状态" clearable>
                <el-option label="正常" value="normal" />
                <el-option label="离线" value="offline" />
                <el-option label="报警" value="alarm" />
                <el-option label="故障" value="fault" />
              </el-select>
            </el-form-item>
          </el-col>
          <!-- 设备类型 -->
          <el-col :span="6">
            <el-form-item label="设备类型">
              <el-select v-model="searchForm.deviceType" multiple placeholder="选择类型" clearable>
                <el-option label="摄像头" value="camera" />
                <el-option label="门禁" value="access" />
                <el-option label="道闸" value="gate" />
                <el-option label="车牌识别" value="license" />
                <el-option label="红外探测器" value="infrared" />
                <el-option label="报警主机" value="alarm" />
              </el-select>
            </el-form-item>
          </el-col>
          <!-- 所属区域 -->
          <el-col :span="4">
            <el-form-item label="所属区域">
              <el-select v-model="searchForm.area" multiple placeholder="选择区域" clearable>
                <el-option label="园区" value="park" />
                <el-option label="楼栋" value="building" />
                <el-option label="楼层" value="floor" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 操作按钮区域 -->
    <el-card class="mb-4">
      <div class="flex justify-between items-center">
        <div>
          <el-button type="primary" @click="handleExport">导出</el-button>
        </div>
        <div>
          <el-button @click="handleConfig">参数配置</el-button>
        </div>
      </div>
    </el-card>

    <!-- 状态统计卡片 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon">
            <el-icon :size="40" color="#67c23a"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statData.total }}台</div>
            <div class="stat-label">启用设备总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon">
            <el-icon :size="40" color="#67c23a"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statData.normal }}台</div>
            <div class="stat-label">正常</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon">
            <el-icon :size="40" color="#909399"><CircleClose /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statData.offline }}台</div>
            <div class="stat-label">离线</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon">
            <el-icon :size="40" color="#e6a23c"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statData.abnormal }}台</div>
            <div class="stat-label">异常</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 统计图表区域 -->
    <el-card class="mb-4">
      <div class="stat-chart-header">
        <el-tabs v-model="statMode" type="border-card">
          <el-tab-pane name="area" label="按区域统计" />
          <el-tab-pane name="building" label="按楼栋统计" />
          <el-tab-pane name="type" label="按设备类型统计" />
        </el-tabs>
        <el-date-picker
          v-model="statTimeRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          clearable
          size="small"
        />
        <el-button @click="handleStatExport" size="small">导出</el-button>
      </div>
      <div class="stat-chart-content">
        <el-skeleton :rows="4" v-loading="statLoading" />
        <div class="stat-chart" v-if="!statLoading">
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="stat-item" v-for="item in statData.areaStat" :key="item.name">
                <div class="stat-item-name">{{ item.name }}</div>
                <div class="stat-item-bar">
                  <div class="stat-bar-bg">
                    <div class="stat-bar-fill" :style="{ width: item.percentage + '%' }">
                      <div class="stat-bar-text">{{ item.percentage }}%</div>
                    </div>
                  </div>
                  <div class="stat-item-value">{{ item.value }}</div>
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="stat-item" v-for="item in statData.typeStat" :key="item.name">
                <div class="stat-item-name">{{ item.name }}</div>
                <div class="stat-item-bar">
                  <div class="stat-bar-bg">
                    <div class="stat-bar-fill" :style="{ width: item.percentage + '%' }">
                      <div class="stat-bar-text">{{ item.percentage }}%</div>
                    </div>
                  </div>
                  <div class="stat-item-value">{{ item.value }}</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-card>

    <!-- 设备列表 -->
    <el-card>
      <el-table v-loading="loading" :data="deviceList" style="width: 100%">
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
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tooltip :content="getStatusText(scope.row.status)" placement="top">
              <el-icon
                :size="24"
                :color="getStatusColor(scope.row.status)"
                :class="{ 'status-icon': true, 'status-anim': isAbnormal(scope.row.status) }"
                @click="handleStatusClick(scope.row)"
              >
                <component :is="getStatusIcon(scope.row.status)" />
              </el-icon>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="启用状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.enabled === '1' ? 'success' : 'info'">
              {{ scope.row.enabled === '1' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="area" label="所属区域" />
        <el-table-column prop="lastUpdateTime" label="最后更新时间" width="160" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="primary" size="small" @click="handleDeviceDetail(scope.row)">详情</el-button>
            <el-button type="danger" size="small" @click="handleAlarm(scope.row)">告警</el-button>
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

    <!-- 状态历史弹窗 -->
    <el-dialog v-model="historyDialogVisible" title="状态变更历史" width="800px">
      <el-form :model="searchHistoryForm" label-width="100px" size="small" class="mb-4">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="searchHistoryForm.timeRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="设备状态">
              <el-select v-model="searchHistoryForm.status" multiple placeholder="选择状态" clearable>
                <el-option label="正常" value="normal" />
                <el-option label="离线" value="offline" />
                <el-option label="报警" value="alarm" />
                <el-option label="故障" value="fault" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="变更原因">
              <el-select v-model="searchHistoryForm.reason" multiple placeholder="选择原因" clearable>
                <el-option label="子系统推送" value="push" />
                <el-option label="轮询检测" value="polling" />
                <el-option label="手动恢复" value="manual" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <el-table :data="statusHistory" style="width: 100%">
        <el-table-column prop="id" label="记录ID" width="100" />
        <el-table-column prop="beforeStatus" label="变更前状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.beforeStatus)">{{ getStatusText(scope.row.beforeStatus) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="afterStatus" label="变更后状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.afterStatus)">{{ getStatusText(scope.row.afterStatus) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="changeTime" label="变更时间" width="160" />
        <el-table-column prop="changeReason" label="变更原因" width="120" />
        <el-table-column prop="operator" label="操作人" width="100" />
        <el-table-column prop="alarmId" label="关联告警ID" width="120">
          <template #default="scope">
            <el-button v-if="scope.row.alarmId" type="text" @click="handleAlarmClick(scope.row.alarmId)">
              {{ scope.row.alarmId }}
            </el-button>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="historyDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="handleHistoryExport">导出</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="SecurityDeviceMonitor">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleCheck, CircleClose, Warning, Monitor } from '@element-plus/icons-vue'

// 响应式数据
const searchForm = reactive({
  keyword: '',
  status: [],
  deviceType: [],
  area: []
})

const searchHistoryForm = reactive({
  timeRange: [],
  status: [],
  reason: []
})

const statMode = ref('area')
const statTimeRange = ref([])
const loading = ref(false)
const statLoading = ref(false)
const historyDialogVisible = ref(false)

const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

// 设备列表数据
const deviceList = ref([
  {
    id: 1,
    name: '园区主入口摄像头',
    sn: 'CAM-20240101-001',
    type: 'camera',
    status: 'normal',
    enabled: '1',
    area: '园区',
    lastUpdateTime: '2024-03-12 10:30:00'
  },
  {
    id: 2,
    name: '消防控制室摄像头',
    sn: 'CAM-20240101-002',
    type: 'camera',
    status: 'offline',
    enabled: '1',
    area: '园区',
    lastUpdateTime: '2024-03-12 09:15:00'
  },
  {
    id: 3,
    name: '配电室摄像头',
    sn: 'CAM-20240101-003',
    type: 'camera',
    status: 'alarm',
    enabled: '1',
    area: '园区',
    lastUpdateTime: '2024-03-12 10:00:00'
  },
  {
    id: 4,
    name: '1号楼门禁',
    sn: 'ACC-20240101-001',
    type: 'access',
    status: 'normal',
    enabled: '1',
    area: '楼栋',
    lastUpdateTime: '2024-03-12 10:25:00'
  },
  {
    id: 5,
    name: '地下车库道闸',
    sn: 'GATE-20240101-001',
    type: 'gate',
    status: 'fault',
    enabled: '1',
    area: '园区',
    lastUpdateTime: '2024-03-12 08:30:00'
  },
  {
    id: 6,
    name: '园区周界红外探测器',
    sn: 'INF-20240101-001',
    type: 'infrared',
    status: 'normal',
    enabled: '1',
    area: '园区',
    lastUpdateTime: '2024-03-12 10:20:00'
  },
  {
    id: 7,
    name: '报警主机',
    sn: 'ALM-20240101-001',
    type: 'alarm',
    status: 'normal',
    enabled: '1',
    area: '园区',
    lastUpdateTime: '2024-03-12 10:15:00'
  },
  {
    id: 8,
    name: '园区主干道摄像头',
    sn: 'CAM-20240101-004',
    type: 'camera',
    status: 'normal',
    enabled: '0',
    area: '园区',
    lastUpdateTime: '2024-03-12 10:10:00'
  },
  {
    id: 9,
    name: '2号楼门禁',
    sn: 'ACC-20240101-002',
    type: 'access',
    status: 'normal',
    enabled: '1',
    area: '楼栋',
    lastUpdateTime: '2024-03-12 10:05:00'
  },
  {
    id: 10,
    name: '车牌识别摄像头',
    sn: 'LIC-20240101-001',
    type: 'license',
    status: 'normal',
    enabled: '1',
    area: '园区',
    lastUpdateTime: '2024-03-12 10:00:00'
  }
])

// 状态历史数据
const statusHistory = ref([
  {
    id: 1,
    beforeStatus: 'normal',
    afterStatus: 'offline',
    changeTime: '2024-03-12 09:15:00',
    changeReason: '轮询检测',
    operator: '系统',
    alarmId: 'ALM-20240312-001'
  },
  {
    id: 2,
    beforeStatus: 'offline',
    afterStatus: 'normal',
    changeTime: '2024-03-12 09:30:00',
    changeReason: '子系统推送',
    operator: '系统',
    alarmId: 'ALM-20240312-002'
  },
  {
    id: 3,
    beforeStatus: 'normal',
    afterStatus: 'alarm',
    changeTime: '2024-03-12 10:00:00',
    changeReason: '子系统推送',
    operator: '系统',
    alarmId: 'ALM-20240312-003'
  }
])

// 统计数据
const statData = ref({
  total: 10,
  normal: 6,
  offline: 1,
  abnormal: 3,
  areaStat: [
    { name: '园区', value: '90%', percentage: 90, total: 10, online: 9 },
    { name: '楼栋', value: '100%', percentage: 100, total: 2, online: 2 },
    { name: '楼层', value: '0%', percentage: 0, total: 0, online: 0 }
  ],
  typeStat: [
    { name: '摄像头', value: '75%', percentage: 75, total: 4, online: 3 },
    { name: '门禁', value: '100%', percentage: 100, total: 2, online: 2 },
    { name: '道闸', value: '0%', percentage: 0, total: 1, online: 0 },
    { name: '红外探测器', value: '100%', percentage: 100, total: 1, online: 1 },
    { name: '报警主机', value: '100%', percentage: 100, total: 1, online: 1 },
    { name: '车牌识别', value: '100%', percentage: 100, total: 1, online: 1 }
  ]
})

// 方法
const handleSearch = () => {
  ElMessage.success('搜索功能已触发')
}

const resetSearch = () => {
  Object.keys(searchForm).forEach(key => {
    searchForm[key] = Array.isArray(searchForm[key]) ? [] : ''
  })
}

const handleSizeChange = (size) => {
  pagination.size = size
}

const handleCurrentChange = (current) => {
  pagination.current = current
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

const getStatusText = (status) => {
  switch (status) {
    case 'normal': return '正常：设备运行正常，无异常事件'
    case 'offline': return '离线：设备网络连接断开'
    case 'alarm': return '报警：设备触发告警事件'
    case 'fault': return '故障：设备运行异常'
    default: return ''
  }
}

const getStatusColor = (status) => {
  switch (status) {
    case 'normal': return '#67c23a'
    case 'offline': return '#909399'
    case 'alarm': return '#e6a23c'
    case 'fault': return '#f56c6c'
    default: return '#67c23a'
  }
}

const getStatusIcon = (status) => {
  switch (status) {
    case 'normal': return CircleCheck
    case 'offline': return CircleClose
    case 'alarm': return Warning
    case 'fault': return Monitor
    default: return CircleCheck
  }
}

const isAbnormal = (status) => {
  return ['offline', 'alarm', 'fault'].includes(status)
}

const handleStatusClick = (row) => {
  historyDialogVisible.value = true
}

const showDeviceDetail = (row) => {
  ElMessage.info(`查看设备详情: ${row.name}`)
}

const handleDeviceDetail = (row) => {
  ElMessage.info(`跳转到设备详情: ${row.name}`)
}

const handleAlarm = (row) => {
  ElMessage.info(`跳转到告警中心: ${row.name}`)
}

const handleAlarmClick = (alarmId) => {
  ElMessage.info(`查看告警详情: ${alarmId}`)
}

const handleExport = () => {
  ElMessage.success('导出功能已触发')
}

const handleStatExport = () => {
  ElMessage.success('统计导出功能已触发')
}

const handleHistoryExport = () => {
  ElMessage.success('历史记录导出功能已触发')
}

const handleConfig = () => {
  ElMessage.info('参数配置功能')
}

// 生命周期
onMounted(() => {
  loading.value = true
  statLoading.value = true
  setTimeout(() => {
    loading.value = false
    statLoading.value = false
  }, 500)
})
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

/* 统计卡片 */
.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  margin-right: 20px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

/* 统计图表 */
.stat-chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stat-chart-content {
  padding: 16px;
}

.stat-item {
  margin-bottom: 20px;
}

.stat-item-name {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.stat-item-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stat-bar-bg {
  flex: 1;
  height: 24px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.stat-bar-fill {
  height: 100%;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.3s;
}

.stat-bar-text {
  font-size: 12px;
  color: white;
  font-weight: bold;
}

.stat-item-value {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  min-width: 80px;
  text-align: right;
}

/* 状态图标动画 */
.status-icon {
  cursor: pointer;
  transition: all 0.3s;
}

.status-icon:hover {
  transform: scale(1.2);
}

.status-anim {
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

/* 分页 */
.pagination-container {
  margin-top: 20px;
  text-align: right;
}
</style>
