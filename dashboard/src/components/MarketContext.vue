<template>
  <el-card class="w-full mb-4">
    <template #header>
      <div class="flex justify-between items-center">
        <span class="text-xl font-bold">市场数据</span>
        <el-button type="primary" size="small" @click="fetchMarketContext">刷新</el-button>
      </div>
    </template>
    <div v-if="loading" class="flex justify-center py-8">
      <el-icon class="is-loading"><svg-icon name="Loading" /></el-icon>
    </div>
    <div v-else-if="error" class="text-center text-red-500 py-8">
      {{ error }}
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <el-card shadow="hover" class="bg-blue-50 dark:bg-blue-900">
        <div class="text-center">
          <div class="text-2xl font-bold">{{ marketContext.sh_index }}</div>
          <div class="text-gray-600 dark:text-gray-300">上证指数</div>
        </div>
      </el-card>
      <el-card shadow="hover" class="bg-green-50 dark:bg-green-900">
        <div class="text-center">
          <div class="text-2xl font-bold">{{ marketContext.sh_ratio }}</div>
          <div class="text-gray-600 dark:text-gray-300">上证指数涨跌幅</div>
        </div>
      </el-card>
      <el-card shadow="hover" class="bg-purple-50 dark:bg-purple-900">
        <div class="text-center">
          <div class="text-2xl font-bold">{{ marketContext.sh_open_ratio }}</div>
          <div class="text-gray-600 dark:text-gray-300">上证指数开盘涨跌幅</div>
        </div>
      </el-card>
      <el-card shadow="hover" class="bg-yellow-50 dark:bg-yellow-900">
        <div class="text-center">
          <div class="text-2xl font-bold">{{ marketContext.sh_k_ratio }}</div>
          <div class="text-gray-600 dark:text-gray-300">上证指数K线涨跌幅</div>
        </div>
      </el-card>
      <el-card shadow="hover" class="bg-red-50 dark:bg-red-900">
        <div class="text-center">
          <div class="text-2xl font-bold">{{ marketContext.vol }}</div>
          <div class="text-gray-600 dark:text-gray-300">市场成交量</div>
        </div>
      </el-card>
      <el-card shadow="hover" class="bg-indigo-50 dark:bg-indigo-900">
        <div class="text-center">
          <div class="text-2xl font-bold">{{ marketContext.amount }}</div>
          <div class="text-gray-600 dark:text-gray-300">市场成交金额</div>
        </div>
      </el-card>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getMarketContext } from '../services/api';

const marketContext = ref({
  sh_index: '-',
  sh_ratio: '-',
  sh_open_ratio: '-',
  sh_k_ratio: '-',
  vol: '-',
  amount: '-',
});
const loading = ref(true);
const error = ref('');

const fetchMarketContext = async () => {
  loading.value = true;
  error.value = '';
  try {
    const response = await getMarketContext();
    marketContext.value = response.data;
  } catch (err) {
    error.value = '获取市场数据失败';
    console.error('获取市场数据失败:', err);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchMarketContext);
</script>