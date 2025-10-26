#!/usr/bin/env python3
"""
RSS收集调度器启动脚本
"""

import os
import sys
import signal
import time
from threading import Event

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.app import create_app
from rss.scheduler import start_scheduler, stop_scheduler
from utils.logger import get_logger

logger = get_logger(__name__)

# 全局变量
shutdown_event = Event()

def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，准备关闭调度器...")
    shutdown_event.set()

def main():
    """主函数"""
    logger.info("启动RSS收集调度器")

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 创建Flask应用（用于配置）
    app = create_app()

    try:
        # 启动调度器
        scheduler = start_scheduler({
            'collect_hour': app.config.get('RSS_COLLECT_HOUR', 5),
            'retention_days': app.config.get('NEWS_RETENTION_DAYS', 7)
        })

        logger.info("调度器启动成功，按 Ctrl+C 停止")

        # 主循环
        while not shutdown_event.is_set():
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("收到键盘中断信号")
    except Exception as e:
        logger.error(f"调度器运行异常: {e}")
    finally:
        # 停止调度器
        logger.info("正在停止调度器...")
        stop_scheduler()
        logger.info("调度器已停止")

if __name__ == '__main__':
    main()