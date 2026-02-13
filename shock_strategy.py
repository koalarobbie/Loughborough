 # -*- coding: utf-8 -*-
# 震荡策略，该策略针对单支股票在一定价格位置进行买入卖出，即当股票低于一定价格位置即买入、买入股票高于一定价格位置即卖出，通过股票的价格波动获利
from xtquant import xtconstant
import time
from datetime import datetime
from xtquant import xtdata
import pandas as pd
import sqlite3
import configparser
from sqlalchemy import create_engine
from DPTrader import *
from ssOrders import *
from loguru import logger
from log_config import *

MODE_NORMAL = 0
MODE_MONITOR= 1
MODE_DEBUG = 2

TARGET_POOL_FILE = "sqlite:///transactions.db"

ORDER_NONE  = 0
ORDER_BUY = 1
ORDER_SELL = 2


 
class Target: 
    def __init__(self):
        self.stock_code = ""
        self.buy_step = 0.0
        self.sell_step = 0.0
        self.vol = 0
        self.buy_times = 0


QUERY_TRANSACTION = 'SELECT * FROM tansactions'
CONFIG_FILE = 'shock.ini'

class ShockStrategy:
    transaction_db = 'sqlite:///transactions.db'
    def __init__(self,mode = 0,max_order = 5):
        self.trader = None
        self.conn = None
        self.transactions = None
        self.mode = mode
        self.max_order = max_order
        self.targets = []
        self.orders = ssOrders()
    
    def __del__(self):
        pass



    def SetTrader(self,trader):
        self.trader = trader
        if not self.trader.connect():
            print(f"[{datetime.now()}] 连接失败")
            return False
        return True


    def ReadConfig(self):
        # 创建 ConfigParser 对象
        config = configparser.ConfigParser()

        # 读取 INI 文件
        config.read(CONFIG_FILE)  # 文件路径

        # 获取所有 section (区块,目标股票)
        targets = []
        sections = config.sections() 
        #对于每个目标股票获取股票的交易阶梯和
        
        for sec in sections:
            target = Target()
            target.stock_code = sec
            target.buy_step = config.getfloat(sec, 'buy_step')
            target.sell_step = config.getfloat(sec, 'sell_step')
            target.vol = config.getint(sec, 'vol')
            targets.append(target)
        return targets

    #策略运行
    def Run(self):
        if self.trader == None:
            print("未设置xttrader！")
            return
        
        self.conn = create_engine(ShockStrategy.transaction_db)
        if self.conn == None:
            print("连接数据库失败！")
            return
        
        
        #读取交易配置
        print("读取配置信息!")
        self.targets = self.ReadConfig()
        #for target in self.targets:
        #    print(target.stock_code,target.buy_step,target.sell_step,target.vol)
        self.orders.Init(self.targets)

        #获取开放交易数据
        self.transactions = pd.read_sql("tansactions", self.conn)
        self.transactions = self.transactions[[ 'id', 'stock_code',  'datetime', 'order_type',  'price',  'volumn', 'status', 'notes']]  

        for i in range(len(self.transactions)): #处理已成的买入交易
            if self.transactions['status'][i] == 0:
                self.orders.Add(self.transactions['stock_code'][i],ssOrder(self.transactions['id'][i],23,self.transactions['stock_code'][i],self.transactions['price'][i],self.transactions['volumn'][i],xtconstant.ORDER_SUCCEEDED))
            
        #处理当前委托的交易
        real_orders = self.trader.query_orders()
        if real_orders:
            for order in real_orders:
                self.orders.Add(order.stock_code,ssOrder(str(order.order_id),order.order_type,order.stock_code,order.price,order.order_volume,order.order_status,order.order_remark))
                                
        order_time = 0 #买入交易次数
        print("###################自动交易开始，打印当前委托和交易情况：###################")
        self.orders.Dump()
        while True:        
            if self.mode > MODE_NORMAL:
                real_orders = self.trader.query_orders()
                print(f"\n\n[{datetime.now()}] ######################################")
                if real_orders:
                    print("当日实时委托（来自券商）：")
                    for ro in real_orders:
                        print(ro.order_id,ro.stock_code,ro.order_type,ro.price,ro.order_volume,ro.order_status,"|",ro.order_remark)
                print("当前存在的已买入未卖出交易")
                print(self.transactions)

            while (msg := self.trader.pop_message()) != None:
                if msg.msg_type == ORDER_MSG:
                    logger.info(f"委托推送,消息ID:{msg.msg_id},消息类型:{msg.order_type},股票代码:{msg.code},交易ID:{msg.order_id},交易价格:{msg.price},交易量:{msg.volume},状态:{msg.status},备注:{msg.remark}")
                    if msg.status == xtconstant.ORDER_REPORTED:
                        pass
                    if msg.status == xtconstant.ORDER_CANCELED:
                        self.orders.Update_Status(msg.code,str(msg.order_id),msg.status,msg.order_type,msg.remark)
                        logger.info(f"委托撤单,消息ID:{msg.msg_id},消息类型:{msg.order_type},股票代码:{msg.code},交易ID:{msg.order_id},交易价格:{msg.price},交易量:{msg.volume},状态:{msg.status},备注:{msg.remark}")
                elif msg.msg_type == DONE_MSG:
                    logger.info(f"成交推送,消息ID:{msg.msg_id},消息类型:{msg.order_type},股票代码:{msg.code},交易ID:{msg.order_id},交易价格:{msg.price},交易量:{msg.volume},状态:{msg.status},备注:{msg.remark}")
                    ret = self.orders.Update_Status(msg.code,str(msg.order_id),msg.status,msg.order_type,msg.remark)
                    logger.info(f"更新委托成交状态,消息ID:{msg.msg_id},消息类型:{msg.order_type},股票代码:{msg.code},交易ID:{msg.order_id},交易价格:{msg.price},交易量:{msg.volume},状态:{msg.status},备注:{msg.remark},状态更新返回:{ret}")
                    if ret > 0: #更新状态成功，则需要更新数据库
                        if msg.order_type == xtconstant.STOCK_BUY:
                            self.transactions.loc[len(self.transactions)] = {'id':datetime.now().strftime("%Y%m%d") + str(msg.order_id),
                                                                                    'stock_code':msg.code,
                                                                                    'datetime':datetime.now().strftime("%Y%m%d%H%M%S"),
                                                                                    'order_type':'buy',
                                                                                    'price':msg.price,
                                                                                    'volumn':msg.volume,
                                                                                    'status':0,
                                                                                    'notes':""
                                                                                    }
                        elif msg.order_type == xtconstant.STOCK_SELL:
                            trans_id = msg.remark
                            self.transactions.loc[self.transactions['id'] == trans_id,'status'] =  1 
                self.transactions.to_sql("tansactions", self.conn, if_exists='replace',index=False)
                self.orders.Dump()
                         
            for target in self.targets:
                real_price = self.trader.get_realtime_price(target.stock_code)
                if real_price != None:
                    #buy_flag,buy_price,sell_flag,sell_price,trans_id,buy_dec_id,sell_dec_id = self.orders.OrderDecision(target.stock_code,self.mode,real_price,target.buy_step,target.sell_step)
                    od = self.orders.OrderDecision(target.stock_code,self.mode,real_price,target.buy_step,target.sell_step)
                if od.GetBuyDecision():# buy_flag and buy_price < 900:# and order_time < self.max_order:
                    if self.trader.query_asset() >= od.GetBuyPrice() * target.vol:
                        logger.info(f"执行买入股票：{target.stock_code},买入价格:{od.GetBuyPrice()},策略ID:{od.GetBuyDecisionId()}")
                        order_id = self.trader.buy(target.stock_code,od.GetBuyPrice(),target.vol)
                        if  order_id is not None:
                            self.orders.Add(target.stock_code,ssOrder(str(order_id),xtconstant.STOCK_BUY,target.stock_code,od.GetBuyPrice(),target.vol,xtconstant.ORDER_REPORTED,""))
                        order_time = order_time + 1
                if  od.GetSellDecision():# sell_flag and sell_price < 900:
                    if self.trader.query_stock_position(target.stock_code,1) >= target.vol:
                        logger.info(f"执行卖出股票：{target.stock_code},卖出价格：{od.GetSellPrice()},策略ID:{od.GetSellDecisionId()}")
                        order_id = self.trader.sell(target.stock_code,od.GetSellPrice(),target.vol,str(od.GetTranId()))
                        if order_id is not None:
                            self.orders.Add(target.stock_code,ssOrder(str(order_id),xtconstant.STOCK_SELL,target.stock_code,od.GetSellPrice(),target.vol,xtconstant.ORDER_REPORTED,od.GetTranId()))
                if od.GetSellCancelDecision():
                    self.trader.cancel_order(int(od.GetMaxSellId()))
                    logger.info(f"撤销卖出委托,股票代码:{target.stock_code},交易ID:{od.GetMaxSellId()}")
                
            if self.mode > MODE_NORMAL:
                self.orders.Dump()
            
            now = datetime.now()
            if now.hour >= 14 and now.minute >= 50:
                break
            time.sleep(60)
        #盘后处理
        logger.info(f"执行尾盘撤单")
        for target in self.targets:
            orders = self.orders.data[target.stock_code]
            for order in orders:
                if order.order_type == xtconstant.STOCK_BUY and order.status == xtconstant.ORDER_REPORTED:
                    self.trader.cancel_order(int(order.order_id))
                    logger.info(f"盘后撤销未成交买入委托,股票代码:{order.stock_code},交易ID:{order.order_id},交易价格:{order.price},交易量:{order.volume},状态:{order.status},备注:{order.ref}")
       
        self.orders.Dump()

# 单例模式
_daemon_instance = None

def get_daemon():
    global _daemon_instance
    if _daemon_instance is None:
        _daemon_instance = ShockStrategy()
    return _daemon_instance


def GetSetting():
    # 创建 ConfigParser 对象
    config = configparser.ConfigParser()

    # 读取 INI 文件
    config.read("config.ini")  # 文件路径
    mode = config.getint('General','mode')
    max_order = config.getint('General','max_order')
    qmt = config.get('General','client_path')
    account_id = config.get('General','ACCOUNT_ID')
    session_id = config.getint('General','SESSION_ID')
    return mode,max_order,account_id,session_id,qmt


# 初始化守护进程
#shock = get_daemon()

if __name__ == "__main__":
    # 配置参数（根据实际情况修改）
    setup_logger()
    (mode,max_order,account_id,session_id,qmt) = GetSetting()
    QMT_PATH = qmt
    SESSION_ID = session_id#123456
    ACCOUNT_ID = account_id#
    print(f"[{datetime.now()}] 启动量化交易程序")
    trader = QuantTrader(QMT_PATH, SESSION_ID, ACCOUNT_ID)
    
    now = datetime.now()
    print(f"datetime方法 - 当前时间: {now.hour:02d}:{now.minute:02d}")
    
    shock = ShockStrategy(mode,max_order)
    if(shock.SetTrader(trader)): 
        shock.Run()

