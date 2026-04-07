<template>
  <el-card class="w-full mb-4">
    <template #header>
      <div class="flex justify-between items-center">
        <span class="text-xl font-bold">目标股票列表</span>
        <el-button type="primary" size="small" @click="fetchTargets">刷新</el-button>
      </div>
    </template>
    <div v-if="loading" class="flex justify-center py-8">
      <el-icon class="is-loading"><svg-icon name="Loading" /></el-icon>
    </div>
    <el-table v-else :data="targets" style="width: 100%" stripe>
      <el-table-column type="index" label="行号" width="80" />
      <el-table-column prop="stock_code" label="股票代码" width="120" />
      <el-table-column prop="buy_step" label="买入阶梯" width="100" />
      <el-table-column prop="sell_step" label="卖出阶梯" width="100" />
      <el-table-column prop="vol" label="数量" width="80" />
      <el-table-column prop="policy" label="策略ID" width="80" />
      <el-table-column prop="down_price" label="地板价" width="100" />
      <el-table-column prop="up_price" label="天花板价" width="100" />
      <el-table-column prop="ma30" label="MA30" width="100" />
      <el-table-column prop="buy_coef" label="买入系数" width="100" />
      <el-table-column label="操作" width="120">
        <template #default="{ row, $index }">
          <el-button 
            type="danger" 
            size="small" 
            @click="handleDelete($index)"
            :loading="deletingIndex === $index"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getTargets, deleteTarget } from '../services/api';
import { ElMessage } from 'element-plus';

const targets = ref([]);
const loading = ref(true);
const deletingIndex = ref(-1);

const fetchTargets = async () => {
  loading.value = true;
  try {
    const response = await getTargets();
    targets.value = response.data;
  } catch (error) {
    console.error('获取目标股票失败:', error);
    ElMessage.error('获取目标股票失败');
  } finally {
    loading.value = false;
  }
};

const handleDelete = async (index) => {
  deletingIndex.value = index;
  try {
    const response = await deleteTarget(index);
    if (response.data.success) {
      ElMessage.success(response.data.message);
      await fetchTargets();
    } else {
      ElMessage.error(response.data.message);
    }
  } catch (error) {
    console.error('删除目标股票失败:', error);
    ElMessage.error('删除目标股票失败');
  } finally {
    deletingIndex.value = -1;
  }
};

onMounted(fetchTargets);
</script>