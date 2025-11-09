"""
日志配置模块
"""
import os
import sys
from loguru import logger
from config import Config


def setup_logger():
    """设置日志配置"""
    # 移除默认处理器
    logger.remove()

    # 确保日志目录存在
    log_dir = os.path.dirname(Config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 控制台输出
    logger.add(
        sys.stdout,
        level=Config.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    # 文件输出
    logger.add(
        Config.LOG_FILE,
        level=Config.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )

    # 错误日志单独文件
    error_log_file = Config.LOG_FILE.replace('.log', '_error.log')
    logger.add(
        error_log_file,
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 week",
        retention="3 months",
        compression="zip",
        encoding="utf-8"
    )

    return logger


# 初始化日志
app_logger = setup_logger()