# -*- coding: utf-8 -*-
# 震荡策略，该策略针对单支股票在一定价格位置进行买入卖出，即当股票低于一定价格位置即买入、买入股票高于一定价格位置即卖出，通过股票的价格波动获利

from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from xtquant.xttype import XtOrder
from xtquant import xtconstant
import time
from datetime import datetime
from xtquant import xtdata

ORDER_MSG = 1
DONE_MSG = 2

class DPMessage():

    def __init__(self,msg_id:str = '',msg_type:int = 0,order_type:int = 0,code:str = '',order_id:str = '',price:float=0,volume:int=0,status:int = 0,remark:str=0):
        self.msg_id = msg_id
        self.msg_type = msg_type
        self.order_type = order_type
        self.code = code
        self.order_id = order_id
        self.price = price
        self.volume = volume
        self.status = status
        self.remark = remark
        

class DPXtQuantTraderCallback(XtQuantTraderCallback):
    def __init__(self):
        self.message_list = []

    def push_message(self,msg:DPMessage):
        self.message_list.append(msg)

    def pop_message(self):
        if len(self.message_list) > 0:
            msg = self.message_list.pop(0)
            return msg
        return None
    
    def on_disconnected(self):
        """
        连接断开
        :return:
        """
        #self.log("connection lost")
        

    def on_stock_order(self, order):
        """
        委托回报推送
        :param order: XtOrder对象
        :return:
        """
        #log_str = "委托回报推送,委托股票代码:{},委托状态:{},委托ID:{}".format(order.stock_code, order.order_status, order.order_sysid)
        #self.log(log_str)
        self.push_message(DPMessage(str(int(datetime.now().timestamp())),ORDER_MSG,order.order_type,order.stock_code,str(order.order_id),order.price,order.order_volume,order.order_status,order.order_remark) )
        #print("on order callback")
    
    def on_stock_asset(self, asset):
        """
        资金变动推送
        :param asset: XtAsset对象
        :return:
        """
        #log_str = "资金变动推送,账户ID:{},现金:{},资产:{}".format(asset.account_id, asset.cash, asset.total_asset)
        #self.log(log_str)
        #print("on asset callback")
        #print(asset.account_id, asset.cash, asset.total_asset)
    
    def on_stock_trade(self, trade):
        """
        成交变动推送
        :param trade: XtTrade对象
        :return:
        """
        #log_str = "成交变动推送,账户ID:{},成交股票代码:{},委托ID:{}".format(trade.account_id, trade.stock_code, trade.order_id)
        #self.log(log_str)
        self.push_message(DPMessage(str(int(datetime.now().timestamp())),DONE_MSG,trade.order_type,trade.stock_code,str(trade.order_id),trade.traded_price,trade.traded_volume,xtconstant.ORDER_SUCCEEDED,trade.order_remark) )
        print("on trade callback")
        #print(trade.account_id, trade.stock_code, trade.order_id)
    
    def on_stock_position(self, position):
        """
        持仓变动推送
        :param position: XtPosition对象
        :return:
        """
        #log_str = "持仓变动推送,股票代码:{},持仓量:{}".format(position.stock_code, position.volume)
        #self.log(log_str)
        print("on position callback")
        #print(position.stock_code, position.volume)
    
    def on_order_error(self, order_error):
        """
        委托失败推送
        :param order_error:XtOrderError 对象
        :return:
        """
        #log_str = "委托失败推送,委托ID:{},错误ID:{},错误信息:{}".format(order_error.order_id, order_error.error_id, order_error.error_msg)
        #self.log(log_str)
        #print("on order_error callback")
        #print(order_error.order_id, order_error.error_id, order_error.error_msg)
    
    def on_cancel_error(self, cancel_error):
        """
        撤单失败推送
        :param cancel_error: XtCancelError 对象
        :return:
        """
        #log_str = "撤单失败推送,委托ID:{},错误ID:{},错误信息:{}".format(cancel_error.order_id, cancel_error.error_id,cancel_error.error_msg)
        #self.log(log_str)
        #print("on cancel_error callback")
        #print(cancel_error.order_id, cancel_error.error_id,
        #cancel_error.error_msg)
    
    def on_order_stock_async_response(self, response):
        """
        异步下单回报推送
        :param response: XtOrderResponse 对象
        :return:
        """
        #log_str = "异步下单回报推送,账户ID:{},委托ID:{},响应序列号:{}".format(response.account_id, response.order_id, response.seq)
        #self.log(log_str)
        #print("on_order_stock_async_response")
        #print(response.account_id, response.order_id, response.seq)
    
    def on_account_status(self, status):
        """
        :param response: XtAccountStatus 对象
        :return:
        """
        #log_str = "账户状态推送,账户ID:{},账户类型:{},账户状态:{}".format(status.account_id, status.account_type, status.status)
        #self.log(log_str)
        print("on_account_status")
        #print(status.account_id, status.account_type, status.status)


class QuantTrader:
    def __init__(self, qmt_path, session_id, account_id):
        self.xt_trader = XtQuantTrader(qmt_path, session_id)
        self.acc = StockAccount(account_id)
        self.callback = DPXtQuantTraderCallback()
        self.connected = False
        xtdata.enable_hello = False

    def connect(self):
        try:
            self.xt_trader.register_callback(self.callback)
            self.xt_trader.start()
            connect_result = self.xt_trader.connect()
            if connect_result != 0:
                raise ConnectionError(f"交易服务器连接失败，错误码: {connect_result}")

            subscribe_result = self.xt_trader.subscribe(self.acc)
            if subscribe_result != 0:
                raise ConnectionError(f"账号订阅失败，错误码: {subscribe_result}")
            self.connected = True
            print(f"[{datetime.now()}] 交易服务器连接成功")
            return True
        except Exception as e:
            print(f"[{datetime.now()}] 连接失败: {e}")
            return False
    
    #买入函数，按价格和买入量执行买入委托
    def buy(self,code,price,volume = 200):
        try:
            fix_result_order_id = self.xt_trader.order_stock(self.acc, code,xtconstant.STOCK_BUY, volume, xtconstant.FIX_PRICE, price, 'strategy_name','remark')
            return fix_result_order_id
        except Exception as e:
            print(f"[{datetime.now()}] 下单失败: {e}")
            print("买入下单失败，股票代码：",code,"委托价格：",price,"买入量：",volume)
            return None
        
    #卖出函数，按价格和买入量执行卖出委托
    def sell(self,code,price,volume = 200,remark=""):
        try:
            fix_result_order_id = self.xt_trader.order_stock(self.acc, code,xtconstant.STOCK_SELL, volume, xtconstant.FIX_PRICE, price, 'strategy_name',remark)
            return fix_result_order_id
        except Exception as e:
            print(f"[{datetime.now()}] 下单失败: {e}")
            print("卖出下单失败，股票代码：",code,"委托价格：",price,"卖出量：",volume,"卖出备注:",remark)
            return None


    def cancel_order(self,order_id):
        try:
            cancel_order_result = self.xt_trader.cancel_order_stock(self.acc, order_id)
            return cancel_order_result
        except Exception as e:
            print(f"[{datetime.now()}] 撤单失败: {e}")
            print("撤单失败，订单号：",order_id)
            return None

    def get_realtime_price(self, stock_code):
        """获取股票实时价格"""
        try:
            quote = xtdata.get_full_tick([stock_code])
            if quote and stock_code in quote:
                return quote[stock_code]['lastPrice']
        except Exception as e:
            print(f"[{datetime.now()}] 获取实时价格失败: {e}")
        return None
    
    #查询委托状态
    #输入：委托号
    #输出：委托状态
    def query_order_status(self,order_id):
        try:
            order = self.xt_trader.query_stock_order(self.acc, order_id)
            if order:
                return order#order.order_status
            else:
                return None
        except Exception as e:
            print(f"[{datetime.now()}] 查询委托状态失败: {e}")
            return None

    #查询当日所有委托状态
    #输入：委托号
    #输出：委托状态
    def query_orders(self):
        try:
            #print("账户：",self.acc)
            orders = self.xt_trader.query_stock_orders(self.acc)
            #print(orders)
            if orders:
                #print("得到当日委托")
                return orders
            #print("查询失败")
            return None
        except Exception as e:
            print(f"[{datetime.now()}] 查询当日所有委托失败: {e}")
            return None
        
    
    def query_positions(self):
        try:
            positions = self.xt_trader.query_stock_positions(self.acc)
            if positions:
                return positions
            return None
        except Exception as e:
            print(f"[{datetime.now()}] 查询当前所有持仓失败: {e}")
            return None
        
    def query_stock_position(self,stock_code:str,type:int = 0): #0返回持仓，1返回可用
        try:
            position = self.xt_trader.query_stock_position(self.acc, stock_code)
            if position:
                if type == 0:
                    return position.volume
                else:
                    return position.can_use_volume
            return 0
        except Exception as e:
            print(f"[{datetime.now()}] 查询股票持仓失败: {e}")
            return 0
        
    def query_asset(self):
        try:
            asset = self.xt_trader.query_stock_asset(self.acc)
            if asset:
                return asset.cash
        except Exception as e:
            print(f"[{datetime.now()}] 查询资产失败: {e}")
            return 0
    
    def pop_message(self):
        msg = self.callback.pop_message()
        return msg