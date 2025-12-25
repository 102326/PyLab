<template>
  <div class="verify-container">
    <el-card class="verify-card">
      <template #header>
        <div class="card-header">
          <h3>👥 教师实名认证</h3>
          <el-tag v-if="status === 0" type="info">未认证</el-tag>
          <el-tag v-else-if="status === 1" type="warning">审核中</el-tag>
          <el-tag v-else-if="status === 2" type="success">已认证</el-tag>
        </div>
      </template>

      <div v-if="status !== 2" class="upload-section">
        <el-alert
            title="请上传二代身份证照片，确保文字清晰、无反光"
            type="info"
            show-icon
            :closable="false"
            class="mb-20"
        />

        <div class="id-card-wrapper">
          <div class="id-card-box">
            <div class="label">身份证人像面</div>
            <div class="upload-area" @click="triggerUpload('front')">
              <img v-if="frontUrl" :src="frontUrl" class="preview-img" />
              <div v-else class="upload-placeholder">
                <el-icon :size="40"><Plus /></el-icon>
                <span>点击上传正面</span>
              </div>
              <input type="file" ref="frontInputRef" @change="(e) => handleFileChange(e, 'front')" style="display: none" accept="image/*"/>
            </div>
            <el-progress v-if="uploadState.front.uploading" :percentage="uploadState.front.percent" :status="uploadState.front.status" />
          </div>

          <div class="id-card-box">
            <div class="label">身份证国徽面</div>
            <div class="upload-area" @click="triggerUpload('back')">
              <img v-if="backUrl" :src="backUrl" class="preview-img" />
              <div v-else class="upload-placeholder">
                <el-icon :size="40"><Plus /></el-icon>
                <span>点击上传反面</span>
              </div>
              <input type="file" ref="backInputRef" @change="(e) => handleFileChange(e, 'back')" style="display: none" accept="image/*"/>
            </div>
            <el-progress v-if="uploadState.back.uploading" :percentage="uploadState.back.percent" :status="uploadState.back.status" />
          </div>
        </div>

        <div class="action-footer">
          <el-button type="primary" size="large" @click="submitVerify" :loading="submitting" :disabled="!isReady">
            提交认证
          </el-button>
        </div>
      </div>

      <div v-else class="verified-info">
        <el-result icon="success" title="已通过认证" sub-title="您已获得教师权限，可以创建课程了">
          <template #extra>
            <el-button type="primary" @click="$router.push('/upload')">去发布课程</el-button>
          </template>
        </el-result>
        <el-descriptions border :column="1" class="info-table">
          <el-descriptions-item label="真实姓名">{{ verifiedData.real_name }}</el-descriptions-item>
          <el-descriptions-item label="身份证号">{{ verifiedData.id_card }}</el-descriptions-item>
        </el-descriptions>
      </div>

    </el-card>
  </div>
</template>

<script setup>
// 1. 补上 reactive
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import request from '@/utils/request';
import * as qiniu from 'qiniu-js';
import { Plus } from '@element-plus/icons-vue';

// 状态管理
const status = ref(0); // 0:未认证, 1:审核中, 2:已认证
const submitting = ref(false);
const frontUrl = ref('');
const backUrl = ref('');
const verifiedData = reactive({ real_name: '', id_card: '' });

// 上传状态
const uploadState = reactive({
  front: { uploading: false, percent: 0, status: '' },
  back: { uploading: false, percent: 0, status: '' }
});

const frontInputRef = ref(null);
const backInputRef = ref(null);

// 触发文件选择
const triggerUpload = (type) => {
  if (type === 'front') frontInputRef.value.click();
  else backInputRef.value.click();
};

// 核心逻辑：七牛云上传 (复用之前的逻辑)
const handleFileChange = async (event, type) => {
  const file = event.target.files[0];
  if (!file) return;

  // 1. 获取上传凭证
  try {
    uploadState[type].uploading = true;
    const res = await request.get('/api/media/token');
    const { token, domain } = res.data.data;

    // 2. 配置七牛上传
    const key = `idcard/${type}_${Date.now()}_${file.name}`;
    const config = { useCdnDomain: true, region: qiniu.region.z1 }; // 注意：这里区域要跟你之前的一致(z1是华北)
    const putExtra = {};

    const observable = qiniu.upload(file, key, token, config, putExtra);

    // 3. 开始上传
    observable.subscribe({
      next: (res) => {
        uploadState[type].percent = Math.floor(res.total.percent);
      },
      error: (err) => {
        ElMessage.error('图片上传失败');
        uploadState[type].uploading = false;
        uploadState[type].status = 'exception';
      },
      complete: (res) => {
        uploadState[type].percent = 100;
        uploadState[type].status = 'success';

        // 拼接完整 URL
        const finalUrl = `${domain}/${res.key}`;
        if (type === 'front') frontUrl.value = finalUrl;
        else backUrl.value = finalUrl;

        uploadState[type].uploading = false;
      }
    });

  } catch (e) {
    console.error(e);
    ElMessage.error('无法获取上传凭证');
    uploadState[type].uploading = false;
  }
};

// 计算属性：是否可以提交
const isReady = computed(() => {
  return frontUrl.value && backUrl.value;
});

// 提交给后端 OCR
const initStatus = async () => {
  try {
    // 页面加载时，先去后端查一次真实状态
    // 建议后端增加一个 GET /api/auth/verify/status 接口，或者复用 /me 接口
    const res = await request.get('/api/auth/me');
    const profile = res.data.data.teacher_profile;
    if (profile) {
      status.value = profile.verify_status; // 0, 1, 2, 3
      if (status.value === 2) {
        verifiedData.real_name = profile.real_name;
        verifiedData.id_card = profile.id_card;
      }
    }
  } catch(e) { console.error(e); }
};

// 【新增】监听 WebSocket 触发的事件
const handleOCRCompleted = (e) => {
  console.log("收到 WebSocket 通知，更新页面状态", e.detail);
  // 直接根据消息更新状态，不需要再查接口
  status.value = e.detail.verify_status; // 应该变成 2
  verifiedData.real_name = e.detail.real_name;
};

onMounted(() => {
  initStatus();
  // 监听全局事件
  window.addEventListener('ocr-completed', handleOCRCompleted);
});

onUnmounted(() => {
  window.removeEventListener('ocr-completed', handleOCRCompleted);
});

const submitVerify = async () => {
  if (!isReady.value) return;
  submitting.value = true;
  try {
    await request.post('/api/auth/verify/idcard', {
      front_url: frontUrl.value,
      back_url: backUrl.value
    });

    ElMessage.success('提交成功，系统正在审核...');

    // 【核心修复】: 绝对不要直接设为 2 (已认证)
    // 而是设为 1 (审核中)，等待 WebSocket 把你变成 2
    status.value = 1;

  } catch (error) {
    // ...
  } finally {
    submitting.value = false;
  }
};
</script>

<style scoped>
.verify-container {
  max-width: 900px;
  margin: 40px auto;
  padding: 0 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.mb-20 {
  margin-bottom: 20px;
}
.id-card-wrapper {
  display: flex;
  gap: 40px;
  justify-content: center;
  margin: 40px 0;
}
.id-card-box {
  width: 320px;
  text-align: center;
}
.label {
  font-weight: bold;
  margin-bottom: 10px;
  color: #606266;
}
.upload-area {
  width: 320px;
  height: 200px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #fafafa;
  transition: 0.3s;
  overflow: hidden;
  position: relative;
}
.upload-area:hover {
  border-color: #409eff;
}
.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #909399;
}
.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.action-footer {
  text-align: center;
  margin-top: 40px;
}
.info-table {
  max-width: 600px;
  margin: 20px auto;
}
</style>