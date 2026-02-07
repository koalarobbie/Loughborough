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


class ssOrder:
    def __init__(self,id:str, type:int, code:str, price:float, volume:int, status:int,ref:str=""):
        self.order_id = id
        self.order_type = type
        self.stock_code = code
        self.price = price
        self.volume = volume
        self.status = status
        self.ref = ref


class ssOrders:
    def __init__(self):
        self.data = {}


    def Init(self,targets:list):
        for target in targets:
            self.data[target.stock_code] = []
    
    def Add(self,code:str, order:ssOrder):
        if code not in self.data.keys():
            self.data[code] = []
        orders = self.data[code]
        if order is not None:
            for od in orders:
                if od.order_id == order.order_id:
                    return
            orders.append(order)
            #更新卖出委托对应的买入委托状态为102(已买在卖)
            if order.order_type == xtconstant.STOCK_SELL:
                for buy_order in orders:
                    if buy_order.order_id == order.ref:
                        buy_order.status = 102 
    
    def Remove(self,code:str, id:str):
        orders = self.data[code]
        if order is not None:
            for order in orders:
                if order.order_id == id:
                    orders.remove(order)

    def Update_Status(self,code:str, id:str, status:int,type:int,ref:str):
        orders = self.data[code]
        ret = -1
        if orders is not None:
            for order in orders:
                if order.order_id == id and order.status != status: #and order.type == type and 
                    order.status = status
                    if order.order_type == xtconstant.STOCK_SELL:
                        ret = self.Update_Status(code,ref,101 ,xtconstant.STOCK_BUY,"") - 1 
                    else:
                        ret = status 
        return ret

    def GetStatus(self,status:int):
        status_dict = {50:"委托", 54: "已撤",56:"成交",101:"已买已卖",102:"已买在卖"}
        try:
            ret = status_dict[status]
        except:
            ret = '其它'
        return ret

    def IsReported(self,code:str, id:str):   #某个ID的委托是否是已报状态
        orders = self.data[code]
        if orders is not None:
            for order in orders:
                if order.order_id == id and order.status == xtconstant.ORDER_REPORTED:
                    return True
        return False

    def OrderDecision(self, code:str,mode:int, real_price:float,buy_step:float,sell_step:float): #判断是否需要执行新的买入卖出交易，以及交易价格是多少
        orders = self.data[code]
        min_buy_price = min_tran_price = 999
        max_buy_price = 0
        min_buy_status = 50
        ret_buy = ret_sell = False
        buy_price = sell_price = 0
        tran_id = ""
        buy_decision_id = 0
        sell_decision_id = 0
        if orders is not None:
            sell_order = []
            for order in orders:#确定最小买入价格，最大买入价格，以及最小成交价格，根据这几个价格来确定是否买入和卖出
                if order.order_type == xtconstant.STOCK_BUY and  order.status == xtconstant.ORDER_REPORTED and order.price < min_buy_price:
                    min_buy_price = order.price
                if order.order_type == xtconstant.STOCK_BUY and  order.status == xtconstant.ORDER_REPORTED and order.price > max_buy_price:
                    max_buy_price = order.price
                if  order.order_type == xtconstant.STOCK_BUY and  (order.status == xtconstant.ORDER_SUCCEEDED  or order.status == 102 ) and order.price < min_tran_price:
                    min_tran_price = order.price
                    tran_id = str(order.order_id)
                    min_buy_status = order.status

            #|min_buy_price |-----|max_buy_price|-------|min_tran_price| 仅当real_price低于min_buy_price或者高于max_buy_price,且max_buy_price与min_tran_price之间有一定差距时，才执行买入卖出操作
            #确定是否需要买入，买入条件，仅当当前价低于最低一笔买入成交和买入委托时，才执行买入
            if real_price < min_tran_price and real_price < min_buy_price: #如果当前价格小于最低成交价，且没有委托的情况下
                ret_buy = True
                if real_price < (min_tran_price - buy_step):
                    buy_price = round(real_price,2)  
                else:
                    buy_price = round(min_tran_price - buy_step,2)
                buy_decision_id = 1
                print("买入策略1：股票代码：",code,"当前价格:",real_price,"最低成交价:",min_tran_price)
            #当当前最高买入价与真实价格之差超过了2倍buy_step时，以当前价-buy_step价格作为买入价
            elif (min_tran_price < 900) and ( real_price > max_buy_price ) and (min_tran_price -  max_buy_price) > (buy_step * 1.8): #如果当前价高于最高委托，且最高委托和最小成交价直接存在空洞
                #buy_price = round(real_price - buy_step,2)
                buy_price = round(max_buy_price +  buy_step,2) if max_buy_price > 0 else round(min_tran_price -  buy_step,2)
                ret_buy = True
                buy_decision_id = 2
                print("买入策略2：股票代码：",code,"当前价格:",real_price,"最高买入价：",max_buy_price,"最低成交价:",min_tran_price)
            #确定是否需要卖出,当最低买入交易未执行卖出，则执行卖出
            if min_buy_status == xtconstant.ORDER_SUCCEEDED:#如果最小买入价格的股票的状态不是在卖就执行卖出操作== xtconstant.ORDER_SUCCEEDED : #如果买入价格最低的买入交易为委托卖出，则卖出标记为True
                ret_sell = True
                if real_price > (min_tran_price + sell_step):
                    sell_price = round(real_price ,2)  
                else:
                    sell_price = round(min_tran_price + sell_step,2)
                sell_decision_id = 3
            return ret_buy,buy_price,ret_sell,sell_price,tran_id,buy_decision_id,sell_decision_id
        else:
            return False,0,False,0,"",0,0

    def Dump(self):
        print("当日委托状态")
        print("股票代码\t 委托ID\t\t委托类型\t价格\t委托量\t委托状态\t备注")
        for key in self.data:
            orders = self.data[key]
            for order in orders:
                print(key,"\t",order.order_id,"\t  ",order.order_type,"\t\t",order.price,"\t",order.volume,"\t",self.GetStatus(order.status),"\t",order.ref)


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

        self.log_file = "running_log.log"
        self.f = open(self.log_file, 'w', encoding='utf-8')

    def __del__(self):
        self.closelog()

    def log(self,log_str):
        now_time = datetime.now()
        str_time = now_time.strftime("%Y-%m-%d %H:%M:%S")
        log_str = str_time + " " + log_str + "\n"
        print(log_str)
        self.f.write(log_str)

    def closelog(self):
        self.f.close()

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
                    self.log(f"委托推送,消息ID:{msg.msg_id},消息类型:{msg.order_type},股票代码:{msg.code},交易ID:{msg.order_id},交易价格:{msg.price},交易量:{msg.volume},状态:{msg.status},备注:{msg.remark}")
                    if msg.status == xtconstant.ORDER_REPORTED:
                        pass
                    if msg.status == xtconstant.ORDER_CANCELED:
                        self.orders.Update_Status(msg.code,str(msg.order_id),msg.status,msg.order_type,msg.remark)
                        self.log(f"委托撤单,消息ID:{msg.msg_id},消息类型:{msg.order_type},股票代码:{msg.code},交易ID:{msg.order_id},交易价格:{msg.price},交易量:{msg.volume},状态:{msg.status},备注:{msg.remark}")
                elif msg.msg_type == DONE_MSG:
                    self.log(f"成交推送,消息ID:{msg.msg_id},消息类型:{msg.order_type},股票代码:{msg.code},交易ID:{msg.order_id},交易价格:{msg.price},交易量:{msg.volume},状态:{msg.status},备注:{msg.remark}")
                    ret = self.orders.Update_Status(msg.code,str(msg.order_id),msg.status,msg.order_type,msg.remark)
                    self.log(f"更新委托成交状态,消息ID:{msg.msg_id},消息类型:{msg.order_type},股票代码:{msg.code},交易ID:{msg.order_id},交易价格:{msg.price},交易量:{msg.volume},状态:{msg.status},备注:{msg.remark},状态更新返回:{ret}")
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
                self.orders.Dump()
                         
            for target in self.targets:
                buy_flag = sell_flag = False
                
                real_price = self.trader.get_realtime_price(target.stock_code)
                if real_price != None:
                    buy_flag,buy_price,sell_flag,sell_price,trans_id,buy_dec_id,sell_dec_id = self.orders.OrderDecision(target.stock_code,self.mode,real_price,target.buy_step,target.sell_step)
                if buy_flag and buy_price < 900:# and order_time < self.max_order:
                    if self.trader.query_asset() >= buy_price * target.vol:
                        self.log(f"执行买入股票：{target.stock_code},买入价格:{buy_price},策略ID:{buy_dec_id}")
                        order_id = self.trader.buy(target.stock_code,buy_price,target.vol)
                        if  order_id is not None:
                            self.orders.Add(target.stock_code,ssOrder(str(order_id),xtconstant.STOCK_BUY,target.stock_code,buy_price,target.vol,xtconstant.ORDER_REPORTED,""))
                        order_time = order_time + 1
                if sell_flag and sell_price < 900:
                    if self.trader.query_stock_position(target.stock_code,1) >= target.vol:
                        self.log(f"执行卖出股票：{target.stock_code},卖出价格：{sell_price},策略ID:{sell_dec_id}")
                        order_id = self.trader.sell(target.stock_code,sell_price,target.vol,str(trans_id))
                        if order_id is not None:
                            self.orders.Add(target.stock_code,ssOrder(str(order_id),xtconstant.STOCK_SELL,target.stock_code,sell_price,target.vol,xtconstant.ORDER_REPORTED,trans_id))
                self.transactions.to_sql("tansactions", self.conn, if_exists='replace',index=False)
            if self.mode > MODE_NORMAL:
                self.orders.Dump()
            
            now = datetime.now()
            if now.hour >= 14 and now.minute >= 50:
                break
            time.sleep(60)
        #盘后处理
        self.log(f"执行尾盘撤单")
        for target in self.targets:
            orders = self.orders.data[target.stock_code]
            for order in orders:
                if order.order_type == xtconstant.STOCK_BUY and order.status == xtconstant.ORDER_REPORTED:
                    self.trader.cancel_order(int(order.order_id))
                    self.log(f"盘后撤销未成交买入委托,股票代码:{order.stock_code},交易ID:{order.order_id},交易价格:{order.price},交易量:{order.volume},状态:{order.status},备注:{order.ref}")
       
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

