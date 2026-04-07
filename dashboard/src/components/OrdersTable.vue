<template>
  <el-card class="w-full mb-4">
    <template #header>
      <div class="flex justify-between items-center">
        <span class="text-xl font-bold">订单信息</span>
        <el-button type="primary" size="small" @click="fetchOrders">刷新</el-button>
      </div>
    </template>
    <div v-if="loading" class="flex justify-center py-8">
      <el-icon class="is-loading"><svg-icon name="Loading" /></el-icon>
    </div>
    <div v-else-if="error" class="text-center text-red-500 py-8">
      {{ error }}
    </div>
    <el-table v-else :data="orderList" style="width: 100%" stripe>
      <el-table-column prop="stock_code" label="股票代码" width="120" />
      <el-table-column prop="order_id" label="订单ID" width="200" />
      <el-table-column prop="order_type" label="订单类型" width="100" />
      <el-table-column prop="price" label="价格" width="100" />
      <el-table-column prop="volume" label="数量" width="100" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="ref" label="备注" />
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { getOrders } from '../services/api';

const orders = ref({});
const loading = ref(true);
const error = ref('');

const orderList = computed(() => {
  const list = [];
  for (const stockCode in orders.value) {
    orders.value[stockCode].forEach(order => {
      list.push({ ...order, stock_code: stockCode });
    });
  }
  return list;
});

const fetchOrders = async () => {
  loading.value = true;
  error.value = '';
  try {
    const response = await getOrders();
    orders.value = response.data;
  } catch (err) {
    error.value = '获取订单失败';
    console.error('获取订单失败:', err);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchOrders);
</script>