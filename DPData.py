# -*- coding: utf-8 -*-
# 震荡策略，该策略针对单支股票在一定价格位置进行买入卖出，即当股票低于一定价格位置即买入、买入股票高于一定价格位置即卖出，通过股票的价格波动获利

from xtquant.xttype import StockAccount
from xtquant.xttype import XtOrder
from xtquant import xtconstant
import time
from datetime import datetime
from xtquant import xtdata
from loguru import logger

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
 

    def get_current_ratio(self, stock_code:str)->float:
        try:
            quote = xtdata.get_full_tick([stock_code])
            if quote and stock_code in quote:
                ratio  = round((quote[stock_code]['lastPrice'] - quote[stock_code]['lastClose']) / quote[stock_code]['lastClose'] , 4)
        except Exception as e:
            print(f"[{datetime.now()}] 获取涨幅失败: {e}")
        return None
    

    def get_current_amount(self)->float:
        try:
            quote = xtdata.get_full_tick(['000001.SH','399001.SZ','399006.SZ'])
            if quote:
                amount_sh  = round(quote['000001.SH']['amount'] / 100000000,2)
                amount_sz  = round(quote['399001.SZ']['amount'] / 100000000,2)
                amount_cy  = round(quote['399006.SZ']['amount'] / 100000000,2)
                return amount_sh + amount_sz + amount_cy
        except Exception as e:
            print(f"[{datetime.now()}] 获取成交金额失败: {e}")
        return None
    

    def get_market_context(self)->float:
        stock_list = ['000001.SH']
        try:
            quote = xtdata.get_full_tick(stock_list)
            if quote:
                ratio  = round((quote['000001.SH']['lastPrice'] - quote['000001.SH']['lastClose']) / quote['000001.SH']['lastClose'] , 4)
                open_ratio  = round((quote['000001.SH']['open'] - quote['000001.SH']['lastClose']) / quote['000001.SH']['lastClose'] , 4)
        except Exception as e:
            print(f"[{datetime.now()}] 获取涨幅失败: {e}")
        return None
    
    def get_open_ratio(self, stock_code:str)->float:
        try:
            quote = xtdata.get_full_tick([stock_code])
            if quote and stock_code in quote:
                open_ratio = round((quote[stock_code]['open'] - quote[stock_code]['lastClose']) / quote[stock_code]['lastClose'] , 4)
                return open_ratio
        except Exception as e:
            print(f"[{datetime.now()}] 获取开盘涨幅失败: {e}")
        return None
    
    def get_k_ratio(self, stock_code:str)->float:
        try:
            quote = xtdata.get_full_tick([stock_code])
            if quote and stock_code in quote:
                k_ratio = round((quote[stock_code]['lastPrice'] - quote[stock_code]['open']) / quote[stock_code]['lastClose'] , 4)
                return k_ratio
        except Exception as e:
            print(f"[{datetime.now()}] 获取K线涨幅失败: {e}")
        return None

    def get_current_volume(self, stock_code:str)->float:
        try:
            quote = xtdata.get_full_tick([stock_code])
            if quote and stock_code in quote:
                volume  = quote[stock_code]['volume']
                return volume
        except Exception as e:
            print(f"[{datetime.now()}] 获取成交量失败: {e}")
        return None
    
    """
    def get_current_amount(self, stock_code:str)->float:
        try:
            quote = xtdata.get_full_tick([stock_code])
            if quote and stock_code in quote:
                amount  = round(quote[stock_code]['amount'] / 100000000,2)
                return amount
        except Exception as e:
            print(f"[{datetime.now()}] 获取成交金额失败: {e}")
        return None
    """


#策略上下文，提供进行策略决策的上下文信息
class Context:
    def __init__(self,datasource:QuantData = None):
        self.sh_index = 0           #上证指数
        self.sh_ratio = 0           #上证指数涨跌幅
        self.sh_open_ratio = 0      #上证指数开盘涨跌幅
        self.sh_k_ratio = 0         #上证指数当前价与开盘价的涨跌幅
        self.vol = 0                #市场成交量
        self.amount = 0             #市场成交金额 
        self.ds = datasource if datasource is not None else QuantData() #数据接口


    def Update_Context(self):
        self.sh_index = self.ds.get_realtime_price('000001.SH')
        self.sh_ratio = self.ds.get_current_ratio('000001.SH')
        self.sh_open_ratio = self.ds.get_open_ratio('000001.SH')
        self.sh_k_ratio = self.ds.get_current_ratio('000001.SH')
        self.vol = self.ds.get_current_volume('000001.SH')
        self.amount = self.ds.get_current_amount()

    
    def Dump_Context(self):
        logger.info(f"上证指数：{self.sh_index}, 上证指数涨跌幅：{self.sh_ratio}, 上证指数开盘涨跌幅：{self.sh_open_ratio}, 上证指数当前价与开盘价的涨跌幅：{self.sh_k_ratio}, 市场成交量：{self.vol}, 市场成交金额：{self.amount}")

