# -*- coding: utf-8 -*-
"""
ShockStrategy客户端，用于访问RESTful接口
支持console模式，可交互式执行命令
"""

import requests
import sys

class SSClient:
    """ShockStrategy客户端，用于访问RESTful接口"""
    
    def __init__(self, host='localhost', port=6519):
        """初始化客户端
        
        Args:
            host: 服务器地址，默认为localhost
            port: 服务器端口，默认为6519
        """
        self.base_url = f'http://{host}:{port}/api'
    
    def get_status(self):
        """获取策略状态"""
        try:
            response = requests.get(f'{self.base_url}/status')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取状态失败: {str(e)}")
            return None
    
    def get_orders(self):
        """获取订单信息"""
        try:
            response = requests.get(f'{self.base_url}/orders')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取订单失败: {str(e)}")
            return None
    
    def get_targets(self):
        """获取目标股票信息"""
        try:
            response = requests.get(f'{self.base_url}/targets')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取目标股票失败: {str(e)}")
            return None
    
    def delete_target(self, index):
        """删除指定索引的target"""
        try:
            response = requests.delete(f'{self.base_url}/targets/{index}')
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"删除目标股票失败: {str(e)}")
            return None

    def enable_target(self, index):
        """启用指定索引的target"""
        try:
            response = requests.post(f'{self.base_url}/targets/{index}/enable')
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"启用目标股票失败: {str(e)}")
            return None

    def disable_target(self, index):
        """禁用指定索引的target"""
        try:
            response = requests.post(f'{self.base_url}/targets/{index}/disable')
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"禁用目标股票失败: {str(e)}")
            return None
    
    def get_market_context(self):
        """获取市场数据"""
        try:
            response = requests.get(f'{self.base_url}/market-context')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取市场数据失败: {str(e)}")
            return None
    
    def print_status(self):
        """打印策略状态"""
        status = self.get_status()
        if status:
            print("\n=== 策略状态 ===")
            print(f"运行状态: {'运行中' if status.get('running') else '已停止'}")
            print(f"线程状态: {'活跃' if status.get('thread_alive') else '非活跃'}")
            print(f"REST服务: {'运行中' if status.get('rest_service_running') else '已停止'}")
    
    def print_orders(self):
        """以列表形式打印订单信息"""
        orders = self.get_orders()
        if orders:
            print("\n=== 订单信息 ===")
            if 'error' in orders:
                print(f"错误: {orders['error']}")
            else:
                print(f"{'股票代码':<10} {'订单ID':<10} {'类型':<4} {'价格':<8} {'数量':<6} {'状态':<10} {'备注':<20}")
                print("-" * 80)
                for stock_code, order_list in orders.items():
                    if not order_list:
                        print(f"{stock_code:<10} {'无订单':<60}")
                    else:
                        for order in order_list:
                            order_type = '买入' if order['order_type'] == 1 else '卖出'
                            print(f"{stock_code:<10} {order['order_id']:<10} {order_type:<4} {order['price']:<8} {order['volume']:<6} {order['status']:<10} {order['ref']:<20}")
                print("-" * 80)
    
    def print_targets(self):
        """以列表形式打印目标股票信息"""
        targets = self.get_targets()
        if targets:
            print("\n=== 目标股票列表 ===")
            print(f"{'行号':<6} {'股票代码':<12} {'买入阶梯':<10} {'卖出阶梯':<10} {'数量':<8} {'策略ID':<8} {'地板价':<10} {'天花板价':<10} {'MA30':<10} {'买入系数':<10} {'启用':<6}")
            print("-" * 120)
            for i, target in enumerate(targets):
                enabled_str = '是' if target.get('enabled', '1') == '1' else '否'
                print(f"{i:<6} {target['stock_code']:<12} {target['buy_step']:<10} {target['sell_step']:<10} {target['vol']:<8} {target['policy']:<8} {target['down_price']:<10} {target['up_price']:<10} {target['ma30']:<10} {target['buy_coef']:<10} {enabled_str:<6}")
            print("-" * 120)
    
    def print_all(self):
        """打印所有信息"""
        self.print_status()
        self.print_orders()
        self.print_targets()
    
    def print_market_context(self):
        """以列表形式打印市场数据"""
        market_context = self.get_market_context()
        if market_context:
            print("\n=== 市场数据 ===")
            if 'error' in market_context:
                print(f"错误: {market_context['error']}")
            else:
                print(f"上证指数: {market_context.get('sh_index')}")
                print(f"上证指数涨跌幅: {market_context.get('sh_ratio')}")
                print(f"上证指数开盘涨跌幅: {market_context.get('sh_open_ratio')}")
                print(f"上证指数当前价与开盘价的涨跌幅: {market_context.get('sh_k_ratio')}")
                print(f"市场成交量: {market_context.get('vol')}")
                print(f"市场成交金额: {market_context.get('amount')}")

def run_console():
    """运行console模式"""
    # 获取服务器地址
    host = input("请输入服务器地址 (默认: localhost): ") or 'localhost'
    port = input("请输入服务器端口 (默认: 6519): ") or '6519'
    
    try:
        port = int(port)
    except ValueError:
        print("端口号必须是整数，使用默认端口 6519")
        port = 6519
    
    # 创建客户端
    client = SSClient(host=host, port=port)
    
    print(f"\n已连接到服务器: {host}:{port}")
    print("进入console模式，输入命令执行操作")
    print("可用命令:")
    print("  status          - 显示策略状态")
    print("  show orders     - 显示订单信息")
    print("  show targets    - 显示目标股票信息")
    print("  del target <索引> - 删除指定索引的目标股票")
    print("  enable target <索引> - 启用指定索引的目标股票")
    print("  disable target <索引> - 禁用指定索引的目标股票")
    print("  market-context   - 显示市场数据")
    print("  quit            - 退出console")
    print()
    
    # 进入console循环
    while True:
        try:
            # 获取用户输入
            user_input = input("ssclient> ").strip()
            
            # 处理空输入
            if not user_input:
                continue
            
            # 拆分命令
            parts = user_input.split()
            command = parts[0]
            
            # 处理quit命令
            if command == 'quit' or command == 'exit':
                print("退出console模式")
                break
            
            # 处理status命令
            elif command == 'status':
                client.print_status()
            
            # 处理show命令
            elif command == 'show':
                if len(parts) < 2:
                    print("错误: show命令需要指定参数 (orders 或 targets)")
                    continue
                sub_command = parts[1]
                if sub_command == 'orders':
                    client.print_orders()
                elif sub_command == 'targets':
                    client.print_targets()
                else:
                    print(f"错误: 未知的show子命令: {sub_command}")
                    print("可用的子命令: orders, targets")
            
            # 处理del命令
            elif command == 'del':
                if len(parts) < 3:
                    print("错误: del命令需要指定参数 (target <索引>)")
                    continue
                if parts[1] == 'target':
                    try:
                        index = int(parts[2])
                        result = client.delete_target(index)
                        if result:
                            if result.get('success'):
                                print(f"成功: {result.get('message')}")
                            else:
                                print(f"失败: {result.get('message')}")
                    except ValueError:
                        print("错误: 索引必须是整数")
                else:
                    print(f"错误: 未知的del子命令: {parts[1]}")
                    print("可用的子命令: target")
            
            # 处理enable命令
            elif command == 'enable':
                if len(parts) < 3:
                    print("错误: enable命令需要指定参数 (target <索引>)")
                    continue
                if parts[1] == 'target':
                    try:
                        index = int(parts[2])
                        result = client.enable_target(index)
                        if result:
                            if result.get('success'):
                                print(f"成功: {result.get('message')}")
                            else:
                                print(f"失败: {result.get('message')}")
                    except ValueError:
                        print("错误: 索引必须是整数")
                else:
                    print(f"错误: 未知的enable子命令: {parts[1]}")
                    print("可用的子命令: target")
            
            # 处理disable命令
            elif command == 'disable':
                if len(parts) < 3:
                    print("错误: disable命令需要指定参数 (target <索引>)")
                    continue
                if parts[1] == 'target':
                    try:
                        index = int(parts[2])
                        result = client.disable_target(index)
                        if result:
                            if result.get('success'):
                                print(f"成功: {result.get('message')}")
                            else:
                                print(f"失败: {result.get('message')}")
                    except ValueError:
                        print("错误: 索引必须是整数")
                else:
                    print(f"错误: 未知的disable子命令: {parts[1]}")
                    print("可用的子命令: target")
            
            # 处理market-context命令
            elif command == 'market-context':
                client.print_market_context()
            
            # 处理help命令
            elif command == 'help' or command == '?':
                print("可用命令:")
                print("  status          - 显示策略状态")
                print("  show orders     - 显示订单信息")
                print("  show targets    - 显示目标股票信息")
                print("  del target <索引> - 删除指定索引的目标股票")
                print("  enable target <索引> - 启用指定索引的目标股票")
                print("  disable target <索引> - 禁用指定索引的目标股票")
                print("  market-context   - 显示市场数据")
                print("  quit            - 退出console")
            
            # 处理未知命令
            else:
                print(f"错误: 未知命令: {command}")
                print("输入 'help' 查看可用命令")
            
            print()  # 打印空行，提高可读性
            
        except KeyboardInterrupt:
            print("\n退出console模式")
            break
        except Exception as e:
            print(f"执行命令时发生错误: {str(e)}")
            print()

def main():
    """主函数"""
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        # 命令行模式
        client = SSClient()
        
        command = sys.argv[1]
        
        if command == "status":
            client.print_status()
        elif command == "show":
            if len(sys.argv) < 3:
                print("使用方法: python ssClient.py show <orders|targets>")
                return
            sub_command = sys.argv[2]
            if sub_command == "orders":
                client.print_orders()
            elif sub_command == "targets":
                client.print_targets()
            else:
                print("无效的子命令，请使用 'orders' 或 'targets'")
        elif command == "market-context":
            client.print_market_context()
        elif command == "del" and len(sys.argv) >= 4 and sys.argv[2] == "target":
            try:
                index = int(sys.argv[3])
                result = client.delete_target(index)
                if result and result.get('success'):
                    print(f"成功: {result.get('message')}")
                else:
                    print(f"失败: {result.get('message', '未知错误')}")
            except ValueError:
                print("无效的索引，请输入数字")
        elif command == "enable" and len(sys.argv) >= 4 and sys.argv[2] == "target":
            try:
                index = int(sys.argv[3])
                result = client.enable_target(index)
                if result and result.get('success'):
                    print(f"成功: {result.get('message')}")
                else:
                    print(f"失败: {result.get('message', '未知错误')}")
            except ValueError:
                print("无效的索引，请输入数字")
        elif command == "disable" and len(sys.argv) >= 4 and sys.argv[2] == "target":
            try:
                index = int(sys.argv[3])
                result = client.disable_target(index)
                if result and result.get('success'):
                    print(f"成功: {result.get('message')}")
                else:
                    print(f"失败: {result.get('message', '未知错误')}")
            except ValueError:
                print("无效的索引，请输入数字")
        else:
            print("无效的命令")
    else:
        # 没有命令行参数，进入console模式
        run_console()

if __name__ == "__main__":
    main()
