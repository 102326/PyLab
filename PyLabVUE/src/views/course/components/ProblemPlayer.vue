<template>
  <div class="flex h-full bg-gray-900 text-white">
    <div class="w-2/5 border-r border-gray-800 flex flex-col bg-gray-900">
      <div class="p-4 border-b border-gray-800 bg-gray-800/50">
        <h2 class="text-lg font-bold flex items-center">
          <el-icon class="mr-2 text-indigo-400"><Document /></el-icon>
          {{ problem?.title || '加载中...' }}
        </h2>
        <div class="flex gap-4 mt-2 text-xs text-gray-500">
          <span>时间限制: {{ problem?.time_limit }}ms</span>
          <span>内存限制: {{ problem?.memory_limit }}MB</span>
        </div>
      </div>

      <div
        class="flex-1 overflow-y-auto p-6 prose prose-invert max-w-none custom-scrollbar"
        v-html="renderedContent"
      ></div>
    </div>

    <div class="flex-1 flex flex-col min-w-0 bg-[#1e1e1e]">
      <div class="h-10 flex items-center justify-between px-4 bg-[#252526] border-b border-black">
        <div class="text-xs text-gray-400 flex items-center">
          <el-icon class="mr-1"><Monitor /></el-icon> main.py
        </div>
        <div class="flex items-center gap-2">
          <el-button type="info" link size="small" @click="resetCode">重置代码</el-button>
        </div>
      </div>

      <div class="flex-1 relative">
        <vue-monaco-editor
          v-if="problem"
          v-model:value="code"
          theme="vs-dark"
          language="python"
          :options="editorOptions"
          class="h-full w-full"
        />
      </div>

      <div class="h-1/3 min-h-[200px] border-t border-black bg-[#1e1e1e] flex flex-col">
        <div class="h-10 px-4 flex items-center justify-between bg-[#252526] border-b border-black">
          <span class="text-xs font-bold text-gray-400">运行结果</span>
          <el-button
            type="primary"
            size="small"
            :loading="submitting"
            @click="handleSubmit"
            color="#0e639c"
            class="!text-white !border-none"
          >
            <el-icon class="mr-1"><CaretRight /></el-icon> 提交运行
          </el-button>
        </div>

        <div class="flex-1 p-4 font-mono text-sm overflow-auto custom-scrollbar">
          <div v-if="!result" class="text-gray-500">等待提交...</div>

          <div v-else class="space-y-2">
            <div class="flex items-center gap-2">
              <span class="text-gray-400">状态:</span>
              <el-tag :type="statusType" effect="dark">{{ result.status }}</el-tag>
            </div>

            <div
              v-if="result.error_msg"
              class="p-3 bg-red-900/30 text-red-300 rounded border border-red-900/50 whitespace-pre-wrap"
            >
              {{ result.error_msg }}
            </div>

            <div v-else-if="result.status === 'AC'" class="text-green-400">
              🎉 恭喜！答案正确。
              <div class="text-xs text-gray-500 mt-1">
                耗时: {{ result.time_cost || 0 }}ms | 内存: {{ result.memory_cost || 0 }}KB
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { Document, Monitor, CaretRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import { OJApi, type Problem, type Submission } from '@/api/oj'

// 引入 Monaco Editor
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'

const props = defineProps<{
  lessonId: number
  problemId: number
}>()

const md = new MarkdownIt()
const problem = ref<Problem | null>(null)
const code = ref('')
const submitting = ref(false)
const result = ref<Submission | null>(null)

const editorOptions = {
  automaticLayout: true,
  fontSize: 14,
  minimap: { enabled: false },
  scrollBeyondLastLine: false,
}

const renderedContent = computed(() => {
  return problem.value ? md.render(problem.value.content) : ''
})

const statusType = computed(() => {
  if (!result.value) return 'info'
  switch (result.value.status) {
    case 'AC':
      return 'success'
    case 'WA':
      return 'warning'
    case 'TLE':
      return 'warning'
    case 'RE':
      return 'danger'
    default:
      return 'info'
  }
})

// 加载题目
const loadProblem = async () => {
  if (!props.problemId) return
  try {
    const data = await OJApi.getProblem(props.problemId)
    problem.value = data
    code.value = data.init_code || '# 请在此输入 Python 代码\nprint("Hello World")'
    result.value = null // 清空上次结果
  } catch (e) {
    ElMessage.error('题目加载失败')
  }
}

// 提交代码
const handleSubmit = async () => {
  if (!problem.value) return
  submitting.value = true
  result.value = null

  try {
    const res = await OJApi.submitCode({
      problem_id: problem.value.id,
      code: code.value,
      language: 'python',
    })
    result.value = res

    if (res.status === 'AC') {
      ElMessage.success('恭喜通过！下一关已解锁')
      // 这里可以触发一个事件通知父组件更新目录状态
    } else {
      ElMessage.warning('未通过，请检查代码')
    }
  } catch (e) {
    ElMessage.error('提交失败')
  } finally {
    submitting.value = false
  }
}

const resetCode = () => {
  if (problem.value) {
    code.value = problem.value.init_code
  }
}

// 监听题目ID变化，自动刷新
watch(() => props.problemId, loadProblem)

onMounted(() => {
  loadProblem()
})
</script>

<style scoped>
/* 滚动条美化 */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 3px;
}

/* Markdown 样式微调 */
:deep(.prose) {
  color: #d1d5db;
}
:deep(.prose h1),
:deep(.prose h2),
:deep(.prose h3) {
  color: #fff;
  margin-top: 1em;
  margin-bottom: 0.5em;
}
:deep(.prose code) {
  color: #e5e7eb;
  background: #374151;
  padding: 0.2em 0.4em;
  border-radius: 4px;
}
:deep(.prose pre) {
  background: #111827;
  padding: 1em;
  border-radius: 8px;
}
</style>
