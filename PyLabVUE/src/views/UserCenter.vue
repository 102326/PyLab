<template>
  <div class="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-3xl mx-auto space-y-6">
      <div class="bg-white shadow rounded-2xl overflow-hidden">
        <div class="bg-gradient-to-r from-blue-500 to-indigo-600 h-32"></div>
        <div class="px-6 pb-6">
          <div class="relative flex justify-between items-end -mt-12 mb-4">
            <div class="flex items-end">
              <el-avatar
                :size="100"
                class="border-4 border-white shadow-lg !text-3xl !bg-indigo-100 !text-indigo-600 select-none"
                :src="userStore.userInfo?.avatar || ''"
              >
                {{ userStore.userInfo?.nickname?.charAt(0) || 'User' }}
              </el-avatar>
              <div class="ml-4 mb-1">
                <h1 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
                  {{ userStore.userInfo?.nickname }}
                  <span
                    class="px-2 py-0.5 text-xs rounded-full text-white transition-colors duration-300"
                    :class="roleBadgeColor"
                  >
                    {{ roleName }}
                  </span>
                </h1>
                <p class="text-sm text-gray-500">ID: {{ userStore.userInfo?.id }}</p>
              </div>
            </div>
            <el-button type="danger" plain size="small" @click="handleLogout">退出登录</el-button>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-white shadow rounded-2xl p-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-4 border-l-4 border-blue-500 pl-3">
            学习中心
          </h3>
          <div class="grid grid-cols-2 gap-4">
            <div
              class="col-span-2 flex items-center justify-between p-4 bg-indigo-50 rounded-xl cursor-pointer transition-all hover:bg-indigo-100 border border-indigo-100 hover:shadow-md group"
              @click="router.push('/chat')"
            >
              <div class="flex items-center gap-3">
                <div
                  class="bg-white p-2 rounded-lg text-indigo-600 group-hover:scale-110 transition-transform"
                >
                  <el-icon class="text-xl"><ChatDotRound /></el-icon>
                </div>
                <div>
                  <div class="font-bold text-indigo-900 text-sm">AI 学习助手</div>
                  <div class="text-xs text-indigo-400">有问题？随时问我</div>
                </div>
              </div>
              <el-icon class="text-indigo-300"><ArrowRight /></el-icon>
            </div>

            <div
              class="flex flex-col items-center justify-center p-6 bg-gray-50 rounded-xl cursor-pointer transition-all hover:bg-blue-50 hover:text-blue-600 hover:shadow-md"
              @click="ElMessage.info('我的课程功能开发中...')"
            >
              <el-icon class="text-blue-500 text-2xl mb-2"><Reading /></el-icon>
              <span>我的课程</span>
            </div>
            <div
              class="flex flex-col items-center justify-center p-6 bg-gray-50 rounded-xl cursor-pointer transition-all hover:bg-blue-50 hover:text-blue-600 hover:shadow-md"
              @click="ElMessage.info('收藏夹功能开发中...')"
            >
              <el-icon class="text-yellow-500 text-2xl mb-2"><Star /></el-icon>
              <span>收藏夹</span>
            </div>
          </div>
        </div>

        <div class="bg-white shadow rounded-2xl p-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-4 border-l-4 border-purple-500 pl-3">
            讲师中心
          </h3>

          <div v-if="isVerifiedTeacher" class="space-y-4 animate-fade-in">
            <div
              class="flex flex-col items-center justify-center p-6 bg-purple-50 rounded-xl cursor-pointer transition-all hover:bg-purple-100 border border-purple-100 hover:shadow-md"
              @click="router.push('/teacher/upload')"
            >
              <el-icon class="text-purple-600 text-2xl mb-2"><Upload /></el-icon>
              <span>发布新课程</span>
            </div>

            <div v-if="myCourses.length > 0" class="mt-4 border-t border-gray-100 pt-4">
              <div class="flex justify-between items-center mb-2 px-1">
                <h4 class="text-sm font-bold text-gray-600">管理已发布课程</h4>
                <el-button link type="primary" size="small" @click="fetchMyCourses">刷新</el-button>
              </div>

              <div class="space-y-2 max-h-60 overflow-y-auto pr-1 custom-scrollbar">
                <div
                  v-for="course in myCourses"
                  :key="course.id"
                  class="flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-white hover:shadow-sm border border-transparent hover:border-gray-200 transition-all group"
                >
                  <div class="truncate flex-1 mr-2">
                    <div class="flex items-center">
                      <span class="text-sm font-medium text-gray-800 truncate">{{
                        course.title
                      }}</span>
                    </div>
                    <div class="flex items-center mt-1">
                      <span
                        class="text-[10px] px-1.5 py-0.5 rounded border"
                        :class="
                          course.is_published
                            ? 'bg-green-50 text-green-600 border-green-100'
                            : 'bg-orange-50 text-orange-600 border-orange-100'
                        "
                      >
                        {{ course.is_published ? '已发布' : '草稿' }}
                      </span>
                    </div>
                  </div>

                  <div class="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <el-button
                      size="small"
                      type="primary"
                      plain
                      @click="router.push(`/teacher/course/${course.id}/edit`)"
                    >
                      <el-icon><Edit /></el-icon>
                    </el-button>

                    <el-button size="small" type="danger" plain @click="handleDeleteCourse(course)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
              </div>
            </div>

            <p v-else class="text-xs text-gray-400 text-center mt-4">您还没有发布任何课程</p>
          </div>

          <div v-else class="flex flex-col items-center justify-center h-full py-4 min-h-[200px]">
            <div v-if="verifyStatus === 1" class="text-center animate-pulse">
              <el-icon class="text-orange-500 text-4xl mb-2"><Timer /></el-icon>
              <p class="text-gray-600 font-medium">讲师资格审核中</p>
              <p class="text-xs text-gray-400 mt-1">系统正在进行 OCR 自动识别...</p>
            </div>

            <div v-else-if="verifyStatus === 3" class="text-center">
              <el-icon class="text-red-500 text-4xl mb-2"><CircleClose /></el-icon>
              <p class="text-gray-600 font-medium">申请被驳回</p>
              <p class="text-xs text-red-400 mt-1">{{ rejectReason }}</p>
              <el-button type="primary" link class="mt-2" @click="router.push('/teacher/verify')"
                >重新申请</el-button
              >
            </div>

            <div v-else-if="role === 1" class="text-center">
              <p class="text-gray-500 text-sm mb-4">完成实名认证，开启讲师之旅</p>
              <el-button type="primary" round @click="router.push('/teacher/verify')">
                申请成为讲师
              </el-button>
            </div>

            <div v-else class="text-center opacity-50">
              <p class="text-sm text-gray-400">当前身份为学员<br />如需发布课程请注册教师账号</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { AuthApi } from '@/api/auth'
import { CourseApi } from '@/api/course'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Reading,
  Star,
  Upload,
  Timer,
  CircleClose,
  ChatDotRound,
  ArrowRight,
  Edit,
  Delete, // [新增] 引入 Delete 图标
} from '@element-plus/icons-vue'
import type { TeacherProfile } from '@/model/auth'

const router = useRouter()
const userStore = useUserStore()

// 本地状态
const teacherProfile = ref<TeacherProfile | null>(null)
const role = ref(0) // 0:学生, 1:老师
const myCourses = ref<any[]>([])

// 刷新数据方法
const fetchLatestData = async () => {
  try {
    const data = await AuthApi.getMe()
    role.value = data.user_info.role
    teacherProfile.value = data.teacher_profile

    // 如果是认证讲师，顺便拉取课程
    if (role.value === 1 && teacherProfile.value?.verify_status === 2) {
      fetchMyCourses()
    }
  } catch (error) {
    console.error('获取用户信息失败', error)
  }
}

// 获取我的课程
const fetchMyCourses = async () => {
  try {
    const res = await CourseApi.getMyCourses()
    myCourses.value = res
  } catch (e) {
    console.error('获取课程失败', e)
  }
}

// [新增] 删除课程处理函数
const handleDeleteCourse = async (course: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除课程《${course.title}》吗？\n删除后不可恢复！`,
      '危险操作',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    await CourseApi.deleteCourse(course.id) // 需确保 api/course.ts 里有 deleteCourse
    ElMessage.success('课程已删除')
    fetchMyCourses() // 刷新列表
  } catch (e) {
    // 用户取消或出错，不做处理
  }
}

// 初始化
onMounted(() => {
  fetchLatestData()
})

// 监听全局数据变化
watch(
  () => userStore.userInfo,
  () => {
    fetchLatestData()
  },
)

// === 计算属性 ===
const verifyStatus = computed(() => teacherProfile.value?.verify_status ?? 0)
const rejectReason = computed(() => teacherProfile.value?.reject_reason || '资料不符合要求')
const isVerifiedTeacher = computed(() => role.value === 1 && verifyStatus.value === 2)

const roleName = computed(() => {
  if (role.value === 9) return '管理员'
  if (role.value === 1) {
    if (verifyStatus.value === 2) return '认证讲师'
    if (verifyStatus.value === 1) return '审核中'
    if (verifyStatus.value === 3) return '未通过'
    return '待认证'
  }
  return '学员'
})

const roleBadgeColor = computed(() => {
  if (role.value === 9) return 'bg-red-500'
  if (role.value === 1) {
    if (verifyStatus.value === 2) return 'bg-purple-600'
    if (verifyStatus.value === 1) return 'bg-orange-400'
    return 'bg-gray-400'
  }
  return 'bg-blue-400'
})

// === 动作 ===
const handleLogout = () => {
  ElMessageBox.confirm('确定退出当前账号吗？', '提示', { type: 'warning' })
    .then(() => {
      userStore.logout()
      ElMessage.success('已退出')
      router.push('/login')
    })
    .catch(() => {})
}
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* 自定义滚动条样式 */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #ddd;
  border-radius: 2px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #ccc;
}
</style>
