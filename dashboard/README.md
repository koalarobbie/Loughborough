# Shock Strategy Dashboard

这是一个基于Vue.js + Element Plus + Tailwind CSS的前端项目，用于展示和管理Shock Strategy的运行状态、订单信息、目标股票列表和市场数据。

## 项目结构

```
dashboard/
├── index.html          # 入口HTML文件
├── package.json        # 项目配置和依赖
├── vite.config.js      # Vite构建工具配置
├── tailwind.config.js  # Tailwind CSS配置
├── postcss.config.js   # PostCSS配置
├── src/
│   ├── main.js         # Vue应用入口
│   ├── App.vue         # 根组件
│   ├── style.css       # 全局样式
│   ├── services/       # API服务
│   │   └── api.js      # API请求封装
│   └── components/     # 组件
│       ├── StatusCard.vue      # 策略状态组件
│       ├── OrdersTable.vue     # 订单信息组件
│       ├── TargetsTable.vue    # 目标股票组件
│       └── MarketContext.vue   # 市场数据组件
└── README.md           # 项目说明
```

## 功能特性

- **策略状态**：显示ShockStrategy的运行状态、线程状态和REST服务状态
- **市场数据**：显示上证指数、涨跌幅、成交量和成交金额等市场信息
- **订单信息**：以表格形式显示所有订单详情，包括股票代码、订单ID、类型、价格、数量、状态和备注
- **目标股票**：以表格形式显示所有目标股票，包括行号、股票代码、买入阶梯、卖出阶梯、数量、策略ID、地板价、天花板价、MA30和买入系数，支持删除操作

## 技术栈

- **前端框架**：Vue 3
- **UI组件库**：Element Plus
- **CSS框架**：Tailwind CSS
- **HTTP客户端**：Axios
- **构建工具**：Vite

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

### 3. 构建生产版本

```bash
npm run build
```

### 4. 预览生产版本

```bash
npm run preview
```

## 配置说明

- **API代理**：在`vite.config.js`中配置了API代理，将`/api`请求代理到`http://localhost:6519`，确保与ShockStrategy的RESTful接口通信
- **Tailwind CSS**：在`tailwind.config.js`中配置了内容路径，确保所有Vue组件都能被Tailwind CSS处理

## 注意事项

- 确保ShockStrategy的RESTful服务已经启动，并且监听在6519端口
- 确保网络连接正常，能够访问ShockStrategy的API接口
- 对于生产环境，建议使用Nginx或Apache等Web服务器部署构建后的静态文件

## 浏览器兼容性

- 支持所有现代浏览器，包括Chrome、Firefox、Safari和Edge
- 不支持IE浏览器

## 许可证

MIT
