<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <header class="bg-white dark:bg-gray-800 shadow-md">
      <div class="container mx-auto px-4 py-4 flex justify-between items-center">
        <h1 class="text-2xl font-bold text-blue-600 dark:text-blue-400">Shock Strategy Dashboard</h1>
        <el-button type="primary" @click="refreshAll">全部刷新</el-button>
      </div>
    </header>
    <main class="container mx-auto px-4 py-6">
      <StatusCard ref="statusCard" />
      <MarketContext ref="marketContext" />
      <OrdersTable ref="ordersTable" />
      <TargetsTable ref="targetsTable" />
    </main>
    <footer class="bg-white dark:bg-gray-800 shadow-md mt-8">
      <div class="container mx-auto px-4 py-4 text-center">
        <p>© {{ new Date().getFullYear() }} Shock Strategy Dashboard</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import StatusCard from './components/StatusCard.vue';
import OrdersTable from './components/OrdersTable.vue';
import TargetsTable from './components/TargetsTable.vue';
import MarketContext from './components/MarketContext.vue';

const statusCard = ref(null);
const ordersTable = ref(null);
const targetsTable = ref(null);
const marketContext = ref(null);

const refreshAll = () => {
  statusCard.value?.fetchStatus();
  ordersTable.value?.fetchOrders();
  targetsTable.value?.fetchTargets();
  marketContext.value?.fetchMarketContext();
};
</script>