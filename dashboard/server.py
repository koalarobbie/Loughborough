# -*- coding: utf-8 -*-
import http.server
import socketserver
import os
import sys

# 定义服务器端口
PORT = 8000

# 改变当前工作目录到脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 处理命令行参数
def get_restful_ip():
    """获取Restful接口的IP地址"""
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        # 默认使用localhost
        return "localhost"

# 生成config.js文件
def generate_config(restful_ip):
    """生成config.js文件，包含Restful接口的IP地址"""
    config_content = f"""// 配置文件
const CONFIG = {{
    RESTFUL_API: 'http://{restful_ip}:6519/api'
}};"""
    with open('config.js', 'w', encoding='utf-8') as f:
        f.write(config_content)
    print(f"已生成config.js文件，Restful API地址: http://{restful_ip}:6519/api")

# 创建请求处理器
class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

# 主函数
def main():
    # 获取Restful接口的IP地址
    restful_ip = get_restful_ip()
    
    # 生成config.js文件
    generate_config(restful_ip)
    
    # 创建服务器
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"服务器运行在 http://localhost:{PORT}")
        print(f"访问 http://localhost:{PORT}/index_cdn.html 查看Dashboard")
        print(f"Restful API地址: http://{restful_ip}:6519/api")
        httpd.serve_forever()

if __name__ == "__main__":
    main()