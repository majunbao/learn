<template>
  <div class="app-container">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon bg-green">
            <el-icon :size="40" color="#fff"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statData.normal }}</div>
            <div class="stat-label">正常</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon bg-gray">
            <el-icon :size="40" color="#fff"><CircleClose /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statData.offline }}</div>
            <div class="stat-label">离线</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon bg-orange">
            <el-icon :size="40" color="#fff"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statData.alarm }}</div>
            <div class="stat-label">报警</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon bg-red">
            <el-icon :size="40" color="#fff"><Monitor /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statData.fault }}</div>
            <div class="stat-label">故障</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 在线率统计 -->
    <el-card class="mb-4">
      <div class="stat-header">
        <div class="stat-title">设备在线率</div>
        <div class="stat-value-big">{{ statData.onlineRate }}%</div>
      </div>
      <div class="stat-chart">
        <div class="chart-container">
          <div class="chart-item">
            <div class="chart-label">摄像头</div>
            <div class="chart-bar">
              <div class="chart-fill" :style="{ width: statData.cameraRate + '%', backgroundColor: '#67c23a' }" />
            </div>
            <div class="chart-value">{{ statData.cameraRate }}%</div>
          </div>
          <div class="chart-item">
            <div class="chart-label">门禁</div>
            <div class="chart-bar">
              <div class="chart-fill" :style="{ width: statData.accessRate + '%', backgroundColor: '#67c23a' }" />
            </div>
            <div class="chart-value">{{ statData.accessRate }}%</div>
          </div>
          <div class="chart-item">
            <div class="chart-label">道闸</div>
            <div class="chart-bar">
              <div class="chart-fill" :style="{ width: statData.gateRate + '%', backgroundColor: '#f56c6c' }" />
            </div>
            <div class="chart-value">{{ statData.gateRate }}%</div>
          </div>
          <div class="chart-item">
            <div class="chart-label">红外探测器</div>
            <div class="chart-bar">
              <div class="chart-fill" :style="{ width: statData.infraredRate + '%', backgroundColor: '#67c23a' }" />
            </div>
            <div class="chart-value">{{ statData.infraredRate }}%</div>
          </div>
          <div class="chart-item">
            <div class="chart-label">报警主机</div>
            <div class="chart-bar">
              <div class="chart-fill" :style="{ width: statData.alarmRate + '%', backgroundColor: '#67c23a' }" />
            </div>
            <div class="chart-value">{{ statData.alarmRate }}%</div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 设备状态网格 -->
    <el-card>
      <div class="grid-header">
        <div class="grid-title">设备状态监控</div>
        <div class="grid-filter">
          <el-select v-model="filterStatus" placeholder="筛选状态" clearable @change="handleFilter">
            <el-option label="全部" value="" />
            <el-option label="正常" value="normal" />
            <el-option label="离线" value="offline" />
            <el-option label="报警" value="alarm" />
            <el-option label="故障" value="fault" />
          </el-select>
          <el-select v-model="filterType" placeholder="筛选类型" clearable @change="handleFilter">
            <el-option label="全部" value="" />
            <el-option label="摄像头" value="camera" />
            <el-option label="门禁" value="access" />
            <el-option label="道闸" value="gate" />
            <el-option label="红外探测器" value="infrared" />
            <el-option label="报警主机" value="alarm" />
          </el-select>
        </div>
      </div>
      <div class="device-grid">
        <div v-for="device in filteredDeviceList" :key="device.id" class="device-card" :class="getDeviceClass(device.status)">
          <div class="device-header">
            <div class="device-name">{{ device.name }}</div>
            <div class="device-status">
              <el-icon :size="20" :color="getStatusColor(device.status)">
                <component :is="getStatusIcon(device.status)" />
              </el-icon>
              <span class="status-text">{{ getStatusText(device.status) }}</span>
            </div>
          </div>
          <div class="device-info">
            <div class="info-item">
              <span class="info-label">类型:</span>
              <span class="info-value">{{ getDeviceTypeText(device.type) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">区域:</span>
              <span class="info-value">{{ device.area }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">SN码:</span>
              <span class="info-value">{{ device.sn }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">最后更新:</span>
              <span class="info-value">{{ device.lastUpdateTime }}</span>
            </div>
          </div>
          <div class="device-actions">
            <el-button type="primary" size="small" @click="handleDetail(device)">详情</el-button>
            <el-button type="danger" size="small" v-if="isAbnormal(device.status)" @click="handleAlarm(device)">告警</el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 状态历史弹窗 -->
    <el-dialog v-model="historyDialogVisible" title="状态变更历史" width="800px">
      <el-table :data="statusHistory" style="width: 100%">
        <el-table-column prop="id" label="记录ID" width="100" />
        <el-table-column prop="beforeStatus" label="变更前状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.beforeStatus)">{{ getStatusText(scope.row.beforeStatus) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="afterStatus" label="变更后状态" width="120">
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
          <el-button type="primary" @click="handleExport">导出</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="SecurityDeviceMonitor">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleCheck, CircleClose, Warning, Monitor } from '@element-plus/icons-vue'

// 响应式数据
const filterStatus = ref('')
const filterType = ref('')
const historyDialogVisible = ref(false)

// 统计数据
const statData = reactive({
  normal: 6,
  offline: 1,
  alarm: 1,
  fault: 2,
  onlineRate: 90,
  cameraRate: 75,
  accessRate: 100,
  gateRate: 0,
  infraredRate: 100,
  alarmRate: 100
})

// 设备列表数据
const deviceList = ref([
  {
    id: 1,
    name: '园区主入口摄像头',
    sn: 'CAM-20240101-001',
    type: 'camera',
    status: 'normal',
    area: '园区',
    lastUpdateTime: '2024-03-12 10:30:00'
  },
  {
    id: 2,
    name: '消防控制室摄像头',
    sn: 'CAM-20240101-002',
    type: 'camera',
    status: 'offline',
    area: '园区',
    lastUpdateTime: '2024-03-12 09:15:00'
  },
  {
    id: 3,
    name: '配电室摄像头',
    sn: 'CAM-20240101-003',
    type: 'camera',
    status: 'alarm',
    area: '园区',
    lastUpdateTime: '2024-03-12 10:00:00'
  },
  {
    id: 4,
    name: '1号楼门禁',
    sn: 'ACC-20240101-001',
    type: 'access',
    status: 'normal',
    area: '楼栋',
    lastUpdateTime: '2024-03-12 10:25:00'
  },
  {
    id: 5,
    name: '地下车库道闸',
    sn: 'GATE-20240101-001',
    type: 'gate',
    status: 'fault',
    area: '园区',
    lastUpdateTime: '2024-03-12 08:30:00'
  },
  {
    id: 6,
    name: '园区周界红外探测器',
    sn: 'INF-20240101-001',
    type: 'infrared',
    status: 'normal',
    area: '园区',
    lastUpdateTime: '2024-03-12 10:20:00'
  },
  {
    id: 7,
    name: '报警主机',
    sn: 'ALM-20240101-001',
    type: 'alarm',
    status: 'normal',
    area: '园区',
    lastUpdateTime: '2024-03-12 10:15:00'
  },
  {
    id: 8,
    name: '园区主干道摄像头',
    sn: 'CAM-20240101-004',
    type: 'camera',
    status: 'normal',
    area: '园区',
    lastUpdateTime: '2024-03-12 10:10:00'
  },
  {
    id: 9,
    name: '2号楼门禁',
    sn: 'ACC-20240101-002',
    type: 'access',
    status: 'normal',
    area: '楼栋',
    lastUpdateTime: '2024-03-12 10:05:00'
  },
  {
    id: 10,
    name: '车牌识别摄像头',
    sn: 'LIC-20240101-001',
    type: 'license',
    status: 'normal',
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

// 计算属性
const filteredDeviceList = computed(() => {
  return deviceList.value.filter(device => {
    const statusMatch = filterStatus.value ? device.status === filterStatus.value : true
    const typeMatch = filterType.value ? device.type === filterType.value : true
    return statusMatch && typeMatch
  })
})

// 方法
const handleFilter = () => {
  // 筛选逻辑
}

const getDeviceClass = (status) => {
  return `device-${status}`
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
    case 'normal': return '正常'
    case 'offline': return '离线'
    case 'alarm': return '报警'
    case 'fault': return '故障'
    default: return status
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

const getDeviceTypeText = (type) => {
  switch (type) {
    case 'camera': return '摄像头'
    case 'access': return '门禁'
    case 'gate': return '道闸'
    case 'infrared': return '红外探测器'
    case 'alarm': return '报警主机'
    case 'license': return '车牌识别'
    default: return type
  }
}

const isAbnormal = (status) => {
  return ['offline', 'alarm', 'fault'].includes(status)
}

const handleDetail = (device) => {
  historyDialogVisible.value = true
}

const handleAlarm = (device) => {
  ElMessage.info(`跳转到告警中心: ${device.name}`)
}

const handleAlarmClick = (alarmId) => {
  ElMessage.info(`查看告警详情: ${alarmId}`)
}

const handleExport = () => {
  ElMessage.success('导出功能已触发')
}

// 生命周期
onMounted(() => {
  // 初始化
})
</script>

<style scoped>
.app-container {
  padding: 20px;
}

.mb-4 {
  margin-bottom: 16px;
}

/* 统计卡片 */
.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  margin-right: 20px;
  padding: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.bg-green {
  background: #67c23a;
}

.stat-icon.bg-gray {
  background: #909399;
}

.stat-icon.bg-orange {
  background: #e6a23c;
}

.stat-icon.bg-red {
  background: #f56c6c;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 16px;
  color: #606266;
}

/* 在线率统计 */
.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stat-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.stat-value-big {
  font-size: 36px;
  font-weight: bold;
  color: #67c23a;
}

.stat-chart {
  padding: 20px;
}

.chart-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-item {
  display: flex;
  align-items: center;
  gap: 20px;
}

.chart-label {
  width: 100px;
  font-size: 14px;
  color: #606266;
}

.chart-bar {
  flex: 1;
  height: 20px;
  background: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
}

.chart-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.3s;
}

.chart-value {
  width: 80px;
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  text-align: right;
}

/* 设备网格 */
.grid-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.grid-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.grid-filter {
  display: flex;
  gap: 10px;
}

.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.device-card {
  padding: 20px;
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  transition: all 0.3s;
}

.device-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.device-normal {
  border-color: #67c23a;
}

.device-offline {
  border-color: #909399;
}

.device-alarm {
  border-color: #e6a23c;
  animation: pulse 1s infinite;
}

.device-fault {
  border-color: #f56c6c;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% {
    border-color: #e6a23c;
  }
  50% {
    border-color: #f56c6c;
  }
  100% {
    border-color: #e6a23c;
  }
}

.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.device-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.device-status {
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-text {
  font-size: 14px;
  color: #606266;
}

.device-info {
  margin-bottom: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.info-label {
  font-size: 12px;
  color: #909399;
}

.info-value {
  font-size: 12px;
  color: #303133;
  font-weight: bold;
}

.device-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
</style>
