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
                <el-option label="故障" value="fault" />
                <el-option label="报警" value="alarm" />
              </el-select>
            </el-form-item>
          </el-col>
          <!-- 设备类型 -->
          <el-col :span="6">
            <el-form-item label="设备类型">
              <el-select v-model="searchForm.deviceType" multiple placeholder="选择类型" clearable>
                <el-option label="高清摄像头" value="camera" />
                <el-option label="球机" value="dome" />
                <el-option label="半球摄像头" value="half" />
                <el-option label="云台摄像头" value="ptz" />
              </el-select>
            </el-form-item>
          </el-col>
          <!-- 所属区域 -->
          <el-col :span="4">
            <el-form-item label="所属区域">
              <el-select v-model="searchForm.area" multiple placeholder="选择区域" clearable>
                <el-option label="园区核心区域" value="core" />
                <el-option label="重要区域" value="important" />
                <el-option label="普通区域" value="normal" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <!-- 时间范围 -->
          <el-col :span="8">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="searchForm.timeRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                clearable
              />
            </el-form-item>
          </el-col>
          <!-- 视频相关 -->
          <el-col :span="8">
            <el-form-item label="视频相关">
              <el-select v-model="searchForm.videoRelated" multiple placeholder="选择条件" clearable>
                <el-option label="视频清晰度" value="resolution">
                  <el-select v-model="searchForm.resolution" placeholder="选择清晰度" clearable>
                    <el-option label="标清" value="sd" />
                    <el-option label="高清" value="hd" />
                    <el-option label="超清" value="uhd" />
                  </el-select>
                </el-option>
                <el-option label="录像类型" value="recordType">
                  <el-select v-model="searchForm.recordType" placeholder="选择类型" clearable>
                    <el-option label="手动录制" value="manual" />
                    <el-option label="自动录制" value="auto" />
                  </el-select>
                </el-option>
                <el-option label="视频异常类型" value="videoException">
                  <el-select v-model="searchForm.videoException" placeholder="选择异常类型" clearable>
                    <el-option label="无视频流" value="noStream" />
                    <el-option label="录像失败" value="recordFail" />
                  </el-select>
                </el-option>
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
          <el-button type="primary" @click="handleMultiView">多画面切换</el-button>
          <el-button @click="handleFavorite">我的收藏</el-button>
          <el-button @click="handleExport">导出</el-button>
        </div>
        <div>
          <el-button @click="handleConfig">参数配置</el-button>
        </div>
      </div>
    </el-card>

    <!-- 视频预览区域 -->
    <el-card>
      <!-- 多画面切换按钮 -->
      <div class="multi-view-controls">
        <el-button-group>
          <el-button :type="viewMode === 'single' ? 'primary' : ''" @click="viewMode = 'single'">单画面</el-button>
          <el-button :type="viewMode === '4' ? 'primary' : ''" @click="viewMode = '4'">4画面</el-button>
          <el-button :type="viewMode === '9' ? 'primary' : ''" @click="viewMode = '9'">9画面</el-button>
          <el-button :type="viewMode === '16' ? 'primary' : ''" @click="viewMode = '16'">16画面</el-button>
        </el-button-group>
        <el-select v-model="viewResolution" placeholder="清晰度" size="small" @change="handleResolutionChange">
          <el-option label="标清" value="sd" />
          <el-option label="高清" value="hd" />
          <el-option label="超清" value="uhd" />
        </el-select>
      </div>

      <!-- 视频预览网格 -->
      <div class="video-grid" :class="`video-grid-${viewMode}`">
        <div v-for="device in deviceList" :key="device.id" class="video-item" @click="handleDeviceClick(device)">
          <div class="video-placeholder">
            <el-icon :size="60" color="#909399"><VideoCamera /></el-icon>
            <div class="video-title">{{ device.name }}</div>
            <div class="video-status">
              <el-tag :type="getStatusType(device.status)" size="small">{{ getStatusText(device.status) }}</el-tag>
            </div>
          </div>
          <div class="video-overlay" v-if="device.status !== 'normal'">
            <el-icon :size="40" color="red"><Warning /></el-icon>
            <div class="overlay-text">{{ getStatusText(device.status) }}</div>
          </div>
          <div class="video-overlay" v-if="device.favorite">
            <el-icon :size="20" color="gold"><StarFilled /></el-icon>
          </div>
        </div>
      </div>

      <!-- 云台控制面板 -->
      <div class="ptz-control" v-if="activeDevice">
        <div class="ptz-title">云台控制 - {{ activeDevice.name }}</div>
        <div class="ptz-controls">
          <div class="ptz-direction">
            <el-button @click="handlePtzUp">↑</el-button>
            <el-button @click="handlePtzDown">↓</el-button>
            <el-button @click="handlePtzLeft">←</el-button>
            <el-button @click="handlePtzRight">→</el-button>
          </div>
          <div class="ptz-zoom">
            <div class="zoom-label">变焦</div>
            <el-slider v-model="zoomLevel" @change="handleZoomChange" :min="0" :max="100" />
          </div>
          <div class="ptz-focus">
            <div class="focus-label">聚焦</div>
            <el-slider v-model="focusLevel" @change="handleFocusChange" :min="0" :max="100" />
          </div>
        </div>
        <div class="ptz-actions">
          <el-button @click="handlePreset">预设点位</el-button>
          <el-button @click="handleCruise">巡航</el-button>
        </div>
      </div>
    </el-card>

    <!-- 统计查看 -->
    <el-card class="mt-4">
      <div class="stat-header">
        <el-tabs v-model="statMode" type="border-card">
          <el-tab-pane name="onlineRate" label="设备在线率" />
          <el-tab-pane name="videoException" label="视频异常次数" />
          <el-tab-pane name="captureCount" label="抓拍数量" />
          <el-tab-pane name="storageDuration" label="录像存储时长" />
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
      <div class="stat-content">
        <el-skeleton :rows="4" v-loading="statLoading" />
        <div class="stat-chart" v-if="!statLoading">
          <div class="stat-item" v-for="item in statData" :key="item.name">
            <div class="stat-item-name">{{ item.name }}</div>
            <div class="stat-item-value">{{ item.value }}</div>
            <el-progress :percentage="item.percentage" :color="item.color" />
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup name="VideoMonitor">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoCamera, Warning, StarFilled } from '@element-plus/icons-vue'

// 响应式数据
const searchForm = reactive({
  keyword: '',
  status: [],
  deviceType: [],
  area: [],
  timeRange: [],
  resolution: '',
  recordType: '',
  videoException: ''
})

const viewMode = ref('single')
const viewResolution = ref('hd')
const activeDevice = ref(null)
const zoomLevel = ref(50)
const focusLevel = ref(50)
const statMode = ref('onlineRate')
const statTimeRange = ref([])
const statLoading = ref(false)

// 设备列表数据
const deviceList = ref([
  {
    id: 1,
    name: '园区主入口摄像头',
    type: 'camera',
    status: 'normal',
    area: 'core',
    favorite: true,
    resolution: '1080P'
  },
  {
    id: 2,
    name: '消防控制室摄像头',
    type: 'dome',
    status: 'normal',
    area: 'core',
    favorite: true,
    resolution: '4K'
  },
  {
    id: 3,
    name: '配电室摄像头',
    type: 'ptz',
    status: 'offline',
    area: 'core',
    favorite: false,
    resolution: '1080P'
  },
  {
    id: 4,
    name: '园区主干道摄像头',
    type: 'camera',
    status: 'normal',
    area: 'important',
    favorite: false,
    resolution: '1080P'
  },
  {
    id: 5,
    name: '1号楼门禁摄像头',
    type: 'half',
    status: 'fault',
    area: 'important',
    favorite: false,
    resolution: '720P'
  },
  {
    id: 6,
    name: '地下车库摄像头',
    type: 'camera',
    status: 'normal',
    area: 'normal',
    favorite: false,
    resolution: '1080P'
  },
  {
    id: 7,
    name: '园区周界摄像头',
    type: 'ptz',
    status: 'alarm',
    area: 'core',
    favorite: true,
    resolution: '4K'
  },
  {
    id: 8,
    name: '贵重设施存放区摄像头',
    type: 'camera',
    status: 'normal',
    area: 'core',
    favorite: false,
    resolution: '4K'
  },
  {
    id: 9,
    name: '2号楼摄像头',
    type: 'dome',
    status: 'normal',
    area: 'important',
    favorite: false,
    resolution: '1080P'
  },
  {
    id: 10,
    name: '园区停车场摄像头',
    type: 'camera',
    status: 'normal',
    area: 'normal',
    favorite: false,
    resolution: '1080P'
  }
])

// 统计数据
const statData = ref([
  { name: '园区核心区域', value: '98%', percentage: 98, color: '#67c23a' },
  { name: '重要区域', value: '95%', percentage: 95, color: '#67c23a' },
  { name: '普通区域', value: '92%', percentage: 92, color: '#e6a23c' },
  { name: '园区全域', value: '95%', percentage: 95, color: '#67c23a' }
])

// 方法
const handleSearch = () => {
  ElMessage.success('搜索功能已触发')
}

const handleMultiView = () => {
  ElMessage.info('多画面切换功能')
}

const handleFavorite = () => {
  ElMessage.info('我的收藏功能')
}

const handleExport = () => {
  ElMessage.success('导出功能已触发')
}

const handleConfig = () => {
  ElMessage.info('参数配置功能')
}

const handleDeviceClick = (device) => {
  activeDevice.value = device
  ElMessage.info(`点击设备: ${device.name}`)
}

const handleResolutionChange = () => {
  ElMessage.info(`清晰度切换至: ${viewResolution.value}`)
}

const getStatusType = (status) => {
  switch (status) {
    case 'normal': return 'success'
    case 'offline': return 'warning'
    case 'fault': return 'info'
    case 'alarm': return 'danger'
    default: return ''
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'normal': return '正常'
    case 'offline': return '离线'
    case 'fault': return '故障'
    case 'alarm': return '报警'
    default: return status
  }
}

const handlePtzUp = () => {
  ElMessage.info('云台向上控制')
}

const handlePtzDown = () => {
  ElMessage.info('云台向下控制')
}

const handlePtzLeft = () => {
  ElMessage.info('云台向左控制')
}

const handlePtzRight = () => {
  ElMessage.info('云台向右控制')
}

const handleZoomChange = () => {
  ElMessage.info(`变焦调整至: ${zoomLevel.value}`)
}

const handleFocusChange = () => {
  ElMessage.info(`聚焦调整至: ${focusLevel.value}`)
}

const handlePreset = () => {
  ElMessage.info('预设点位功能')
}

const handleCruise = () => {
  ElMessage.info('巡航功能')
}

const handleStatExport = () => {
  ElMessage.success('统计导出功能已触发')
}

// 生命周期
onMounted(() => {
  statLoading.value = true
  setTimeout(() => {
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

.mt-4 {
  margin-top: 16px;
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

/* 多画面控制 */
.multi-view-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

/* 视频网格 */
.video-grid {
  display: grid;
  gap: 16px;
}

.video-grid-single {
  grid-template-columns: repeat(1, 1fr);
}

.video-grid-4 {
  grid-template-columns: repeat(2, 1fr);
}

.video-grid-9 {
  grid-template-columns: repeat(3, 1fr);
}

.video-grid-16 {
  grid-template-columns: repeat(4, 1fr);
}

.video-item {
  position: relative;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
}

.video-item:hover {
  border-color: #409eff;
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.3);
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  background: #f5f7fa;
}

.video-title {
  margin-top: 10px;
  font-size: 14px;
  color: #606266;
}

.video-status {
  margin-top: 10px;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
}

.overlay-text {
  margin-top: 10px;
}

/* 云台控制 */
.ptz-control {
  margin-top: 20px;
  padding: 16px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.ptz-title {
  font-weight: bold;
  margin-bottom: 16px;
  color: #606266;
}

.ptz-controls {
  display: flex;
  gap: 20px;
  align-items: center;
}

.ptz-direction {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 5px;
}

.ptz-zoom,
.ptz-focus {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.zoom-label,
.focus-label {
  font-size: 12px;
  color: #606266;
}

.ptz-actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
}

/* 统计查看 */
.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stat-content {
  padding: 16px;
}

.stat-chart {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-item {
  padding: 16px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.stat-item-name {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.stat-item-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}
</style>
