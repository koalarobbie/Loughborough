# -*- coding: utf-8 -*-
# 测试ShockStrategy RESTful接口

from shock_strategy import ShockStrategy
import time

# 创建一个模拟的Trader类，用于测试
class MockTrader:
    def __init__(self):
        self.connected = False
    
    def connect(self):
        self.connected = True
        print("MockTrader connected")
        return True
    
    def get_realtime_price(self, stock_code):
        return 10.0
    
    def query_asset(self):
        return 100000.0
    
    def query_orders(self):
        return None
    
    def pop_message(self):
        return None

# 创建ShockStrategy实例
strategy = ShockStrategy()

# 设置模拟的Trader
mock_trader = MockTrader()
strategy.SetTrader(mock_trader)

# 启动策略和RESTful服务
strategy.Start()

# 等待服务启动
time.sleep(2)

print("ShockStrategy服务已启动，RESTful接口已可用")
print("您可以使用以下命令测试/api/orders接口:")
print("python ssClient.py show orders")

# 保持程序运行
while True:
    time.sleep(1)
