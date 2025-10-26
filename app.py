#!/usr/bin/env python3
"""
RSSInfomation - 基于微信公众号的RSS科技/AI新闻收集和展示系统
主应用入口文件
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.app import create_app

def main():
    """主函数"""
    app = create_app()

    # 获取配置中的端口
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()