<template>
  <div class="upload-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>资源上传 (教师端)</span>
        </div>
      </template>

      <el-form label-width="80px">
        <el-form-item label="视频标题">
          <el-input v-model="videoTitle" placeholder="请输入视频标题" />
        </el-form-item>

        <el-form-item label="选择文件">
          <input type="file" ref="fileInput" @change="handleFileSelected" style="display: none" />
          <el-button type="primary" @click="$refs.fileInput.click()">选择视频文件</el-button>
          <span class="file-name" v-if="selectedFile">{{ selectedFile.name }}</span>
        </el-form-item>

        <el-form-item label="上传进度" v-if="uploading">
          <el-progress :percentage="uploadPercent" :status="uploadStatus" />
        </el-form-item>

        <el-form-item>
          <el-button type="success" @click="startUpload" :disabled="!selectedFile || uploading">
            开始上传
          </el-button>
        </el-form-item>
      </el-form>

      <div class="result-area" v-if="videoUrl">
        <p>上传成功！播放地址：</p>
        <a :href="videoUrl" target="_blank">{{ videoUrl }}</a>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import * as qiniu from 'qiniu-js';
//引入封装好的 request
import request from '@/utils/request';
import { ElMessage } from 'element-plus';

const videoTitle = ref('');
const selectedFile = ref(null);
const uploading = ref(false);
const uploadPercent = ref(0);
const uploadStatus = ref(''); // 'success' | 'exception'
const videoUrl = ref('');

const handleFileSelected = (event) => {
  const file = event.target.files[0];
  if (file) {
    selectedFile.value = file;
    // 如果没填标题，自动填充文件名
    if (!videoTitle.value) {
      videoTitle.value = file.name.replace(/\.[^/.]+$/, "");
    }
  }
};

const startUpload = async () => {
  if (!videoTitle.value) {
    ElMessage.warning('请输入标题');
    return;
  }

  uploading.value = true;
  uploadPercent.value = 0;

  try {
    // [修改 2] 使用 request 发送请求
    // 拦截器会自动添加 Authorization: Bearer xxxx，解决 401 问题
    const res = await request.get('/api/media/token');

    // 注意：axios 响应拦截器如果直接返回 response，这里取值是 res.data
    const { token, domain } = res.data.data;

    const key = `videos/${Date.now()}_${selectedFile.value.name}`;

    // [修改 3] 七牛云存储区域配置
    const config = {
      useCdnDomain: true,
      // 七牛云区域对照表：
      // z0: 华东-浙江
      // z1: 华北-河北  <-- 你是华北，选这个
      // z2: 华南-广东
      // na0: 北美
      region: qiniu.region.z1
    };

    const putExtra = {
      customVars: { 'x:name': videoTitle.value }
    };

    const observable = qiniu.upload(selectedFile.value, key, token, config, putExtra);

    observable.subscribe({
      next: (res) => {
        uploadPercent.value = Math.floor(res.total.percent);
      },
      error: (err) => {
        console.error(err);
        ElMessage.error('上传失败: ' + err.message);
        uploading.value = false;
        uploadStatus.value = 'exception';
      },
      complete: async (res) => {
        uploadPercent.value = 100;
        uploadStatus.value = 'success';

        try {
          // [修改 4] 保存到数据库也使用 request
          await request.post('/api/media/videos', {
            title: videoTitle.value,
            file_key: res.key,
            file_hash: res.hash,
            file_size: res.fsize,
            duration: 0
          });

          ElMessage.success('发布成功！');
          videoUrl.value = `${domain}/${res.key}`;
          uploading.value = false;
        } catch (dbErr) {
          // 错误已经在 request 拦截器里弹窗了，这里可以不处理，或者做特定逻辑
          console.error(dbErr);
        }
      }
    });

  } catch (e) {
    // request 拦截器会处理 401 跳转，这里主要捕获其他异常
    console.error(e);
    uploading.value = false;
  }
};
</script>

<style scoped>
.upload-container {
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
}
.file-name {
  margin-left: 10px;
  color: #666;
}
.result-area {
  margin-top: 20px;
  padding: 10px;
  background: #f0f9eb;
  border: 1px solid #c2e7b0;
  border-radius: 4px;
}
</style>