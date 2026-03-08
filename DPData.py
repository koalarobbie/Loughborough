# -*- coding: utf-8 -*-
# 震荡策略，该策略针对单支股票在一定价格位置进行买入卖出，即当股票低于一定价格位置即买入、买入股票高于一定价格位置即卖出，通过股票的价格波动获利

from xtquant.xttype import StockAccount
from xtquant.xttype import XtOrder
from xtquant import xtconstant
import time
from datetime import datetime
from xtquant import xtdata


class QuantData:
    def __init__(self):
        pass

    def get_realtime_price(self, stock_code):
        """获取股票实时价格"""
        try:
            quote = xtdata.get_full_tick([stock_code])
            if quote and stock_code in quote:
                return quote[stock_code]['lastPrice']
        except Exception as e:
            print(f"[{datetime.now()}] 获取实时价格失败: {e}")
        return None
    
    def get_mean_price(self, stock_code):
        try:
            quote = xtdata.get_full_tick([stock_code])
            if quote and stock_code in quote:
                mean = round((quote[stock_code]['amount'] / (quote[stock_code]['volume'] *100)),3) if quote[stock_code]['volume'] > 0 else 0
                return mean
        except Exception as e:
            print(f"[{datetime.now()}] 获取均价失败: {e}")
        return None
 

    