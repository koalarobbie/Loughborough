 # -*- coding: utf-8 -*-
# 震荡策略，该策略针对单支股票在一定价格位置进行买入卖出，即当股票低于一定价格位置即买入、买入股票高于一定价格位置即卖出，通过股票的价格波动获利
from xtquant import xtconstant,xtdata
import time
from datetime import datetime
import pandas as pd
import sqlite3
import configparser
from sqlalchemy import create_engine
from DPTrader import *
from DPData import *
from loguru import logger
from log_config import *
from misc import *
import threading
import json
from flask import Flask, jsonify, Response
from target import Target
from flask_cors import CORS
# 延迟导入ssOrders和ssOrder，避免循环导入
#ssOrders = None
#ssOrder = None
from ssOrders import ssOrders, ssOrder

MODE_NORMAL = 0
MODE_MONITOR= 1
MODE_DEBUG = 2

TARGET_POOL_FILE = "sqlite:///transactions.db"

ORDER_NONE  = 0
ORDER_BUY = 1
ORDER_SELL = 2


STATE_TRADE = 575
STATE_CLOSING = 890
STATE_CLOSING_DONE = 895
STATE_CLOSED = 900

 
QUERY_TRANSACTION = 'SELECT * FROM tansactions'
CONFIG_FILE = 'shock.ini'

class ShockStrategy:
    transaction_db = 'sqlite:///transactions.db'
    def __init__(self,mode = 0,max_order = 5):
        global ssOrders, ssOrder
        if ssOrders is None:
            from ssOrders import ssOrders, ssOrder
        self.trader = None
        self.conn = None
        self.transactions = None
        self.mode = mode
        self.max_order = max_order
        self.targets = []
        self.orders = ssOrders()
        self.data_source = QuantData()
        self.market_context = Context(self.data_source)
        self._thread = None
        self._running = False
        # RESTful服务相关
        self._rest_app = None
        self._rest_thread = None
        self._rest_running = False
    
    def __del__(self):
        self.Stop()
        self.StopRestService()
        pass


    def SetOrders(self):
        self.orders = ssOrders()


    def SetTrader(self,trader):
        self.trader = trader
        if not self.trader.connect():
            print(f"[{datetime.now()}] 连接失败")
            return False
        return True


    def ReadConfig(self):
        """
        读取配置文件，解析目标股票信息
        
        功能：
        - 从配置文件中读取所有目标股票的交易参数
        - 为每个股票创建 Target 对象并设置相关属性
        - 计算并设置每个股票的 MA30 指标值
        
        返回值：
        - list[Target]: 包含所有目标股票信息的列表
        """
        # 创建 ConfigParser 对象，用于解析 INI 格式配置文件
        config = configparser.ConfigParser()

        # 读取配置文件
        config.read(CONFIG_FILE)  # 配置文件路径

        # 初始化目标股票列表
        targets = []
        # 获取配置文件中所有的 section (每个 section 对应一个目标股票)
        sections = config.sections() 
        
        # 遍历每个目标股票，解析其交易参数
        for sec in sections:
            # 创建 Target 对象存储股票信息
            target = Target()
            # 设置股票代码（使用 section 名称作为股票代码）
            target.stock_code = sec
            # 读取买入阶梯价格
            target.buy_step = config.getfloat(sec, 'buy_step')
            # 读取卖出阶梯价格
            target.sell_step = config.getfloat(sec, 'sell_step')
            # 读取交易数量
            target.vol = config.getint(sec, 'vol')
            # 读取策略 ID（如果配置中存在），默认为 0
            target.policy = config.getint(sec, 'policy') if config.has_option(sec, 'policy') else 0
            # 读取买入地板价（如果配置中存在），默认为 0
            target.down_price = config.getfloat(sec, 'down_price') if config.has_option(sec, 'down_price') else 0
            # 读取买入天花板价（如果配置中存在），默认为 999
            target.up_price = config.getfloat(sec, 'up_price') if config.has_option(sec, 'up_price') else 999
            # 计算并设置当前 MA30 指标值
            target.ma30 = get_current_ma30(sec)
            # 打印配置信息（已注释）
            #print(f"读取配置 - 股票代码:{target.stock_code}, 买入阶梯:{target.buy_step}, 卖出阶梯:{target.sell_step}, 交易数量:{target.vol}, 策略ID:{target.policy}, 买入地板价:{target.down_price}, 买入天花板价:{target.up_price}, 当前MA30价:{target.ma30}")
            #print(f"读取配置 - 股票代码:{target.stock_code}, 买入阶梯:{target.buy_step}, 卖出阶梯:{target.sell_step}, 交易数量:{target.vol}, 策略ID:{target.policy}, 买入地板价:{target.down_price}, 买入天花板价:{target.up_price}")
            # 将目标股票添加到列表中
            targets.append(target)
        
        # 返回目标股票列表
        return targets


    def ReverseResponse(self): 
        real_price = self.trader.get_realtime_price('131810.SZ')
        position = self.trader.query_asset()
        vol = int(position / 1000) * 10
        fix_result_order_id = self.trader.sell('131810.SZ', real_price, vol,'逆回购申购')
        logger.info(f"执行逆回购申购,股票代码:131810.SZ,交易ID:{fix_result_order_id},交易价格:{real_price},交易量:{vol},状态:申购中,备注:逆回购申购")
    
    def Start(self):
        """启动守护进程模式"""
        if self._thread is not None and self._thread.is_alive():
            logger.info("策略已经在运行中")
            return False
        
        if self.trader == None:
            logger.error("未设置xttrader！")
            return False
        
        self._running = True
        self._thread = threading.Thread(target=self.Run, daemon=True)
        self._thread.start()
        logger.info("策略守护进程已启动")
        
        # 启动RESTful服务
        self.StartRestService()
        return True
    
    def Stop(self):
        """停止守护进程"""
        if self._thread is not None and self._thread.is_alive():
            self._running = False
            self._thread.join(timeout=10)
            logger.info("策略守护进程已停止")
        else:
            logger.info("策略未在运行")

    
    def _init_rest_app(self):
        """初始化RESTful应用"""
        self._rest_app = Flask(__name__)
        # 初始化CORS，允许所有跨域请求
        CORS(self._rest_app)
        
        @self._rest_app.route('/api/status', methods=['GET'])
        def get_status():
            """获取策略运行状态"""
            status = {
                'running': self._running,
                'thread_alive': self._thread is not None and self._thread.is_alive(),
                'rest_service_running': self._rest_running
            }
            response = jsonify(status)
            
            # 添加CORS头
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        @self._rest_app.route('/api/orders', methods=['GET'])
        def get_orders():
            """获取orders对象信息"""
            if not hasattr(self, 'orders') or not self.orders:
                response = jsonify({'error': 'Orders not initialized'})
            else:
                orders_data = {}
                for key in self.orders.data:
                    orders_data[key] = []
                    orders = self.orders.data[key]
                    for order in orders:
                        # 映射订单状态到中文含义
                        status_map = {
                            50: '已报',
                            54: '已撤',
                            56: '已成',
                            57: '废单',
                            101: '已买已卖',
                            102: '已买在卖'
                        }
                        status_text = status_map.get(order.status, str(order.status))
                        
                        order_info = {
                            'stock_code': str(key),
                            'order_id': str(order.order_id),
                            'order_type': str(order.order_type),
                            'price': '{:.2f}'.format(order.price) if isinstance(order.price, (int, float)) else str(order.price),
                            'volume': str(order.volume),
                            'status': status_text,
                            'ref': str(order.ref)
                        }
                        orders_data[key].append(order_info)
                #print(f"当前订单数据: {orders_data}")  # 打印订单数据到控制台
                # 使用json.dumps序列化数据，然后返回Response对象
                try:
                    json_data = json.dumps(orders_data, ensure_ascii=False)
                    response = Response(json_data, mimetype='application/json')
                except Exception as e:
                    logger.error(f"JSON序列化失败: {str(e)}")
                    response = jsonify({'error': f'JSON序列化失败: {str(e)}'})
            
            # 添加CORS头
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        @self._rest_app.route('/api/targets', methods=['GET'])
        def get_targets():
            """获取targets列表"""
            targets_data = []
            for target in self.targets:
                target_info = {
                    'stock_code': str(target.stock_code),
                    'buy_step': '{:.2f}'.format(target.buy_step) if isinstance(target.buy_step, (int, float)) else str(target.buy_step),
                    'sell_step': '{:.2f}'.format(target.sell_step) if isinstance(target.sell_step, (int, float)) else str(target.sell_step),
                    'vol': str(target.vol),
                    'policy': str(target.policy),
                    'down_price': '{:.2f}'.format(target.down_price) if isinstance(target.down_price, (int, float)) else str(target.down_price),
                    'up_price': '{:.2f}'.format(target.up_price) if isinstance(target.up_price, (int, float)) else str(target.up_price),
                    'ma30': '{:.2f}'.format(target.ma30) if isinstance(target.ma30, (int, float)) else str(target.ma30),
                    'buy_coef': '{:.2f}'.format(target.buy_coef) if isinstance(target.buy_coef, (int, float)) else str(target.buy_coef)
                }
                targets_data.append(target_info)
            # 使用json.dumps序列化数据，然后返回Response对象
            try:
                json_data = json.dumps(targets_data, ensure_ascii=False)
                response = Response(json_data, mimetype='application/json')
            except Exception as e:
                logger.error(f"JSON序列化失败: {str(e)}")
                response = jsonify({'error': f'JSON序列化失败: {str(e)}'})
            
            # 添加CORS头
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        @self._rest_app.route('/api/targets/<int:index>', methods=['DELETE'])
        def delete_target(index):
            """删除指定索引的target"""
            success, deleted_target = self.DeleteTarget(index)
            if success:
                response = jsonify({'success': True, 'message': f'已删除目标股票: {deleted_target.stock_code}'})
            else:
                response = jsonify({'success': False, 'message': '无效的目标股票索引'})
                response.status_code = 404
            
            # 添加CORS头
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        @self._rest_app.route('/api/market-context', methods=['GET'])
        def get_market_context():
            """获取当前市场数据"""
            try:
                # 更新市场上下文数据
                self.market_context.Update_Context()
                
                # 构建市场数据字典
                market_data = {
                    'sh_index': str(self.market_context.sh_index),
                    'sh_ratio': '{:.4f}'.format(self.market_context.sh_ratio) if isinstance(self.market_context.sh_ratio, (int, float)) else str(self.market_context.sh_ratio),
                    'sh_open_ratio': '{:.4f}'.format(self.market_context.sh_open_ratio) if isinstance(self.market_context.sh_open_ratio, (int, float)) else str(self.market_context.sh_open_ratio),
                    'sh_k_ratio': '{:.4f}'.format(self.market_context.sh_k_ratio) if isinstance(self.market_context.sh_k_ratio, (int, float)) else str(self.market_context.sh_k_ratio),
                    'vol': str(self.market_context.vol),
                    'amount': '{:.2f}'.format(self.market_context.amount) if isinstance(self.market_context.amount, (int, float)) else str(self.market_context.amount)
                }
                
                # 使用json.dumps序列化数据，然后返回Response对象
                json_data = json.dumps(market_data, ensure_ascii=False)
                response = Response(json_data, mimetype='application/json')
            except Exception as e:
                logger.error(f"获取市场数据失败: {str(e)}")
                response = jsonify({'error': f'获取市场数据失败: {str(e)}'})
            
            # 添加CORS头
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
    
    def StartRestService(self):
        """启动RESTful服务"""
        if self._rest_running:
            logger.info("RESTful服务已经在运行中")
            return False
        
        self._init_rest_app()
        self._rest_running = True
        self._rest_thread = threading.Thread(
            target=self._rest_app.run, 
            kwargs={'host': '0.0.0.0', 'port': 6519, 'debug': False}, 
            daemon=True
        )
        self._rest_thread.start()
        logger.info("RESTful服务已启动，监听端口6519")
        return True
    
    def StopRestService(self):
        """停止RESTful服务"""
        if self._rest_running:
            self._rest_running = False
            # Flask的开发服务器无法优雅停止，这里我们只标记为停止状态
            logger.info("RESTful服务已停止")
        else:
            logger.info("RESTful服务未在运行")
    
    def DeleteTarget(self, index):
        """删除指定索引的target"""
        if 0 <= index < len(self.targets):
            deleted_target = self.targets.pop(index)
            logger.info(f"删除目标股票: {deleted_target.stock_code}")
            return True, deleted_target
        else:
            logger.error(f"无效的目标股票索引: {index}")
            return False, None


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
                self.orders.Add(order.stock_code,ssOrder(traderid2orderid(order.order_id),order.order_type,order.stock_code,order.price,order.order_volume,order.order_status,order.order_remark))
                                
        order_time = 0 #买入交易次数
        print("###################自动交易开始，打印当前委托和交易情况：###################")
        self.orders.Dump()
        
        state = 0
        closing_done = 0
        while self._running:
            now = datetime.now()
            state =now.hour * 60 + now.minute
            if state >= STATE_CLOSED:
                break
            if state < STATE_TRADE:
                time.sleep(60)
                continue

            try:     
                if self.mode > MODE_NORMAL:
                    real_orders = self.trader.query_orders()
                    print(f"\n\n[{datetime.now()}] ######################################")
                    if real_orders:
                        print("当日实时委托（来自券商）：")
                        for ro in real_orders:
                            print(ro.order_id,ro.stock_code,ro.order_type,ro.price,ro.order_volume,ro.order_status,"|",ro.order_remark)
                    print("当前存在的已买入未卖出交易")
                    print(self.transactions)
                
                self.market_context.Update_Context()
                self.market_context.Dump_Context()

                #获取消息推送，更新交易状态
                message_flag = 0
                while (msg := self.trader.pop_message()) != None:
                    message_flag = 1
                    if msg.msg_type == ORDER_MSG:
                        logger.info(f"委托推送,消息ID:{msg.msg_id},消息类型:{msg.order_type},股票代码:{msg.code},交易ID:{msg.order_id},交易价格:{msg.price},交易量:{msg.volume},状态:{msg.status},备注:{msg.remark}")
                        if msg.status == xtconstant.ORDER_REPORTED:
                            pass
                        if msg.status == xtconstant.ORDER_CANCELED:
                            ret = self.orders.Update_Status(msg.code,traderid2orderid(msg.order_id),msg.status,msg.order_type,msg.remark)
                            logger.info(f"委托撤单,消息ID:{msg.msg_id},消息类型:{msg.order_type},股票代码:{msg.code},交易ID:{msg.order_id},交易价格:{msg.price},交易量:{msg.volume},状态:{msg.status},备注:{msg.remark},状态更新返回:{ret}")
                    elif msg.msg_type == DONE_MSG:
                        logger.info(f"成交推送,消息ID:{msg.msg_id},消息类型:{msg.order_type},股票代码:{msg.code},交易ID:{msg.order_id},交易价格:{msg.price},交易量:{msg.volume},状态:{msg.status},备注:{msg.remark}")
                        ret = self.orders.Update_Status(msg.code,traderid2orderid(msg.order_id),msg.status,msg.order_type,msg.remark)
                        logger.info(f"更新委托成交状态,消息ID:{msg.msg_id},消息类型:{msg.order_type},股票代码:{msg.code},交易ID:{msg.order_id},交易价格:{msg.price},交易量:{msg.volume},状态:{msg.status},备注:{msg.remark},状态更新返回:{ret}")
                        if ret > 0: #更新状态成功，则需要更新数据库
                            if msg.order_type == xtconstant.STOCK_BUY:
                                self.transactions.loc[len(self.transactions)] = {'id':traderid2orderid(msg.order_id),
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
                
                if message_flag == 1:
                    self.transactions.to_sql("tansactions", self.conn, if_exists='replace',index=False)
                    self.orders.Dump()

                #交易委托
                if state < STATE_CLOSING:
                    for target in self.targets:
                        real_price = self.trader.get_realtime_price(target.stock_code)
                        if real_price != None:
                            od = self.orders.OrderDecision(target,self.mode,real_price,target.buy_step,target.sell_step)
                        if od.GetBuyDecision() and od.GetBuyPrice() > target.down_price and od.GetBuyPrice() < target.up_price:# buy_flag and buy_price < 900:# and order_time < self.max_order:
                            if self.trader.query_asset() >= od.GetBuyPrice() * target.vol:
                                logger.info(f"执行买入股票：{target.stock_code},策略ID:{od.GetBuyDecisionId()},当前价格:{real_price},买入价格:{od.GetBuyPrice()},买入系数:{od.GetBuyCoef()}")
                                order_id = self.trader.buy(target.stock_code,od.GetBuyPrice(),target.vol)
                                if  order_id is not None:
                                    self.orders.Add(target.stock_code,ssOrder(traderid2orderid(order_id),xtconstant.STOCK_BUY,target.stock_code,od.GetBuyPrice(),target.vol,xtconstant.ORDER_REPORTED,""))
                                order_time = order_time + 1
                        if  od.GetSellDecision():# sell_flag and sell_price < 900:
                            if self.trader.query_stock_position(target.stock_code,1) >= target.vol:
                                logger.info(f"执行卖出股票：{target.stock_code},当前价格:{real_price},卖出价格：{od.GetSellPrice()},策略ID:{od.GetSellDecisionId()}")
                                order_id = self.trader.sell(target.stock_code,od.GetSellPrice(),target.vol,str(od.GetTranId()))
                                if order_id is not None:
                                    self.orders.Add(target.stock_code,ssOrder(traderid2orderid(order_id),xtconstant.STOCK_SELL,target.stock_code,od.GetSellPrice(),target.vol,xtconstant.ORDER_REPORTED,od.GetTranId()))
                        if od.GetSellCancelDecision():
                            self.trader.cancel_order(orderid2traderid(od.GetSellCancelId()))
                            logger.info(f"撤销卖出委托,股票代码:{target.stock_code},交易ID:{orderid2traderid(od.GetSellCancelId())}")
                        #if od.GetBuyCancelDecision():
                        #    self.trader.cancel_order(int(od.GetBuyCancelId()))
                        #    logger.info(f"撤销买入委托,股票代码:{target.stock_code},交易ID:{od.GetBuyCancelId()}")

                
                time.sleep(60)
            except Exception as e:
                logger.error(f"运行过程中发生异常: {str(e)}")
                time.sleep(60)

            if state >= STATE_CLOSING and closing_done == 0:        
                #盘后处理
                logger.info(f"执行尾盘撤单")
                for target in self.targets:
                    orders = self.orders.data[target.stock_code]
                    for order in orders:
                        if order.order_type == xtconstant.STOCK_BUY and order.status == xtconstant.ORDER_REPORTED:
                            self.trader.cancel_order(orderid2traderid(order.order_id))
                            logger.info(f"盘后撤销未成交买入委托,股票代码:{order.stock_code},交易ID:{orderid2traderid(order.order_id)},交易价格:{order.price},交易量:{order.volume},状态:{order.status},备注:{order.ref}")
            
                #盘后购买逆回购
                time.sleep(10)
                self.ReverseResponse()
                closing_done = 1
            
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
shock = get_daemon()

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
    
    #shock = ShockStrategy(mode,max_order)
    #shock = get_daemon()
    #shock.SetOrders()
    if(shock.SetTrader(trader)): 
        shock.Start()
        # 主线程保持运行，等待用户输入或其他操作
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在停止策略...")
            shock.Stop()