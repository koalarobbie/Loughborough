# -*- coding: utf-8 -*-
import http.server
import socketserver
import os

# 定义服务器端口
PORT = 8000

# 改变当前工作目录到脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 创建请求处理器
Handler = http.server.SimpleHTTPRequestHandler

# 创建服务器
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"服务器运行在 http://localhost:{PORT}")
    print(f"访问 http://localhost:{PORT}/index_cdn.html 查看Dashboard")
    httpd.serve_forever()