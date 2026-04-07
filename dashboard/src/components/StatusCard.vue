<template>
  <el-card class="w-full mb-4">
    <template #header>
      <div class="flex justify-between items-center">
        <span class="text-xl font-bold">策略状态</span>
        <el-button type="primary" size="small" @click="fetchStatus">刷新</el-button>
      </div>
    </template>
    <div v-if="loading" class="flex justify-center py-8">
      <el-icon class="is-loading"><svg-icon name="Loading" /></el-icon>
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <el-card shadow="hover" class="bg-blue-50 dark:bg-blue-900">
        <div class="text-center">
          <div class="text-2xl font-bold">{{ status.running ? '运行中' : '已停止' }}</div>
          <div class="text-gray-600 dark:text-gray-300">运行状态</div>
        </div>
      </el-card>
      <el-card shadow="hover" class="bg-green-50 dark:bg-green-900">
        <div class="text-center">
          <div class="text-2xl font-bold">{{ status.thread_alive ? '活跃' : '非活跃' }}</div>
          <div class="text-gray-600 dark:text-gray-300">线程状态</div>
        </div>
      </el-card>
      <el-card shadow="hover" class="bg-purple-50 dark:bg-purple-900">
        <div class="text-center">
          <div class="text-2xl font-bold">{{ status.rest_service_running ? '运行中' : '已停止' }}</div>
          <div class="text-gray-600 dark:text-gray-300">REST服务</div>
        </div>
      </el-card>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getStatus } from '../services/api';

const status = ref({
  running: false,
  thread_alive: false,
  rest_service_running: false,
});
const loading = ref(true);

const fetchStatus = async () => {
  loading.value = true;
  try {
    const response = await getStatus();
    status.value = response.data;
  } catch (error) {
    console.error('获取状态失败:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchStatus);
</script>