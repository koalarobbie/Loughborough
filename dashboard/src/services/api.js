import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

export const getStatus = () => api.get('/status');
export const getOrders = () => api.get('/orders');
export const getTargets = () => api.get('/targets');
export const deleteTarget = (index) => api.delete(`/targets/${index}`);
export const getMarketContext = () => api.get('/market-context');

export default api;