 # -*- coding: utf-8 -*-
from xtquant import xtconstant
import time
from datetime import datetime
from xtquant import xtdata
import pandas as pd
from loguru import logger

class PriceWindows():
    def __init__(self,min_buy:float = 999, max_buy:float = 0, min_tran:float = 999, min_sell:float = 999, max_sell:float = 0,min_buy_status:int = 50):
        self.min_buy = min_buy
        self.max_buy = max_buy
        self.min_tran = min_tran
        self.min_sell = min_sell
        self.max_sell = max_sell
        self.min_buy_status = min_buy_status
        self.max_sell_id = ""

    def SetMinBuy(self,price:float):
        self.min_buy = price

    def SetMaxBuy(self,price:float):
        self.max_buy = price

    def SetMinTran(self,price:float):    
        self.min_tran = price

    def SetMinSell(self,price:float):
        self.min_sell = price  

    def SetMaxSell(self,price:float, id:str = ""):  
        self.max_sell = price  
        self.max_sell_id = id
    
    def SetMinBuyStatus(self,status:int):
        self.min_buy_status = status

    def GetMinBuy(self):
        return self.min_buy

    def GetMaxBuy(self):   
        return self.max_buy

    def GetMinTran(self):
        return self.min_tran   

    def GetMinSell(self):
        return self.min_sell

    def GetMaxSell(self):
        return self.max_sell
    
    def GetMinBuyStatus(self):
        return self.min_buy_status

    def GetMaxSellId(self):
        return self.max_sell_id

    def MinBuyStatusIsDone(self):
        return (True if  self.min_buy_status == xtconstant.ORDER_SUCCEEDED else False)
    
    
     
class ssOderDecision:
    def __init__(self,buy_decision:bool = False, sell_decision:bool = False,buy_cancel_decision:bool = False,sell_cancel_decision:bool = False, buy_price:float = 0, sell_price:float = 0):
        self.buy_decision = buy_decision
        self.sell_decision = sell_decision
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.buy_decision_id = 0
        self.sell_decision_id = 0
        self.tran_id = ""
        self.buy_cancel_decision = buy_cancel_decision
        self.sell_cancel_decision = sell_cancel_decision
        self.max_sell_id = ""

    def SetBuyDecision(self,decision:bool, decision_id:int,price:float = 0):
        self.buy_decision = decision
        self.buy_decision_id = decision_id
        self.buy_price = price

    def SetSellDecision(self,decision:bool, decision_id:int,price:float = 0):
        self.sell_decision = decision
        self.sell_decision_id = decision_id
        self.sell_price = price

    def SetTranId(self,tran_id:str):
        self.tran_id = tran_id

    def SetBuyPrice(self,price:float):
        self.buy_price = price
    
    def SetSellPrice(self,price:float):
        self.sell_price = price
    
    def SetPrice(self,buy_price:float, sell_price:float):
        self.buy_price = buy_price
        self.sell_price = sell_price
    
    def SetBuyCancelDecision(self,decision:bool):
        self.buy_cancel_decision = decision

    def SetSellCancelDecision(self,decision:bool, id:str = ""):
        self.sell_cancel_decision = decision
        self.max_sell_id = id

    def SetMaxSellId(self,id:str):
        self.max_sell_id = id

    def GetMaxSellId(self):
        return self.max_sell_id

    def GetBuyDecision(self):
        return (True if (self.buy_decision and self.buy_price < 900) else False)
    
    def GetBuyPrice(self):
        return self.buy_price

    def GetSellPrice(self):
        return self.sell_price
    
    def GetSellDecision(self):
        return (True if (self.sell_decision and self.sell_price < 900) else False)
    
    def GetBuyDecisionId(self):
        return self.buy_decision_id 
    
    def GetSellDecisionId(self):
        return self.sell_decision_id

    def GetTranId(self):    
        return self.tran_id

    def GetBuyCancelDecision(self):
        return self.buy_cancel_decision 
    
    def GetSellCancelDecision(self):        
        return self.sell_cancel_decision

    def GetMaxSellId(self):
        return self.max_sell_id

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
        pw = PriceWindows()
        od = ssOderDecision()
        buy_price = sell_price = 0

        if orders is not None:
            sell_order = []
            for order in orders:#确定价格窗口： 最小买入价格，最大买入价格，以及最小成交价格，根据这几个价格来确定是否买入和卖出
                if order.order_type == xtconstant.STOCK_BUY and  order.status == xtconstant.ORDER_REPORTED and order.price < pw.GetMinBuy():
                    pw.SetMinBuy(order.price)
                if order.order_type == xtconstant.STOCK_BUY and  order.status == xtconstant.ORDER_REPORTED and order.price > pw.GetMaxBuy():
                    pw.SetMaxBuy(order.price)
                if  order.order_type == xtconstant.STOCK_BUY and  (order.status == xtconstant.ORDER_SUCCEEDED  or order.status == 102 ) and order.price < pw.GetMinTran():
                    pw.SetMinTran(order.price)
                    pw.SetMinBuyStatus(order.status)
                    od.SetTranId(str(order.order_id))
                if order.order_type == xtconstant.STOCK_SELL and  order.status == xtconstant.ORDER_REPORTED and order.price < pw.GetMinSell():
                    pw.SetMinSell(order.price)
                if order.order_type == xtconstant.STOCK_SELL and  order.status == xtconstant.ORDER_REPORTED and order.price > pw.GetMaxSell():
                    pw.SetMaxSell(order.price,str(order.order_id))

                
            #|min_buy_price |-----|max_buy_price|-------|min_tran_price| 仅当real_price低于min_buy_price或者高于max_buy_price,且max_buy_price与min_tran_price之间有一定差距时，才执行买入卖出操作
            #确定是否需要买入，买入条件，仅当当前价低于最低一笔买入成交和买入委托时，才执行买入
            if real_price < pw.GetMinTran() and real_price < pw.GetMinBuy(): #如果当前价格小于最低成交价，且没有委托的情况下
                buy_price = round(real_price,2) if real_price < (pw.GetMinTran() - buy_step) else round(pw.GetMinTran() - buy_step,2)
                od.SetBuyDecision(True, 1,buy_price)
                logger.info(f"买入策略1：股票代码：{code},当前价格:{real_price},最低成交价:{pw.GetMinTran() },最低买入价:{pw.GetMinBuy()}")
            #当当前最高买入价与真实价格之差超过了2倍buy_step时，以当前价-buy_step价格作为买入价
            elif (pw.GetMinTran() < 900) and ( real_price > pw.GetMaxBuy() ) and (pw.GetMinTran() -  pw.GetMaxBuy()) > (buy_step * 1.8): #如果当前价高于最高委托，且最高委托和最小成交价直接存在空洞
                buy_price = round(pw.GetMaxBuy() +  buy_step,2) if pw.GetMaxBuy() > 0 else round(pw.GetMinTran() -  buy_step,2)
                od.SetBuyDecision(True, 2,buy_price)
                logger.info(f"买入策略2：股票代码：{code},当前价格:{real_price},最高买入价：{pw.GetMaxBuy()},最低成交价:{pw.GetMinTran()}")
            #确定是否需要卖出,当最低买入交易未执行卖出，则执行卖出
            if  pw.MinBuyStatusIsDone():#如果最小买入价格的股票的状态不是在卖就执行卖出操作== xtconstant.ORDER_SUCCEEDED : #如果买入价格最低的买入交易为委托卖出，则卖出标记为True
                sell_price = round(round(real_price ,2) ) if real_price > (pw.GetMinTran() + sell_step) else round(pw.GetMinTran() + sell_step,2)
                od.SetSellDecision(True, 3,sell_price)
                logger.info(f"卖出策略：股票代码：{code},当前价格:{real_price},最低成交价:{pw.GetMinTran()},卖出价格:{sell_price}")
            #确定是否需要撤单，撤卖单的条件是，最高卖单价比当前价高2个sell_step
            if  pw.GetMaxSell() - real_price > (sell_step * 2):
                od.SetSellCancelDecision(True,pw.GetMaxSellId())
                logger.info(f"撤销卖单策略：股票代码：{code},当前价格:{real_price},最高卖出价:{pw.GetMaxSell()}")
            
            return od

        else:
            return False,0,False,0,"",0,0

    def Dump(self):
        print("当日委托状态")
        print("股票代码\t 委托ID\t\t委托类型\t价格\t委托量\t委托状态\t备注")
        for key in self.data:
            orders = self.data[key]
            for order in orders:
                print(key,"\t",order.order_id,"\t  ",order.order_type,"\t\t",order.price,"\t",order.volume,"\t",self.GetStatus(order.status),"\t",order.ref)