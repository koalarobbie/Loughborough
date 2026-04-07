# -*- coding: utf-8 -*-
# 目标股票类

class Target: 
    def __init__(self):
        self.stock_code = ""  # 股票代码
        self.buy_step = 0.0   # 买入价格阶梯，即当股票价格比上次买入价格低buy_step时，触发买入
        self.sell_step = 0.0  # 卖出价格阶梯，即当股票价格比上次卖入价格高sell_step时，触发卖出
        self.vol = 0          # 每次买入卖出的数量
        self.buy_times = 0    # 买入次数
        self.policy = 0       # 标的遵循的策略ID
        self.down_price = 0.0 # 买入的地板价，即当股票价格比地板价低时，不再买入
        self.up_price = 0.0   # 买入的天花板价，即当股票价格比天花板价高时，不再买入
        self.ma30 = -1        # 30日均线价格
        self.buy_coef = 1.0   # 买入系数,买入阶梯价*买入系数为实际买入阶梯价
