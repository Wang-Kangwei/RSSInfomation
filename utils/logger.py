"""
日志配置工具
"""

import os
import logging
import logging.handlers
from logging.handlers import RotatingFileHandler
import colorlog

def setup_logging(app):
    """设置应用日志"""

    # 创建日志目录
    log_dir = app.config.get('LOG_DIR', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 获取日志级别
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有处理器
    root_logger.handlers.clear()

    # 配置文件处理器
    log_file = os.path.join(log_dir, 'rss_information.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=app.config.get('LOG_MAX_BYTES', 10 * 1024 * 1024),  # 10MB
        backupCount=app.config.get('LOG_BACKUP_COUNT', 5)
    )
    file_handler.setLevel(log_level)

    # 配置控制台处理器 (带颜色)
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(log_level)

    # 配置日志格式
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # 控制台使用彩色格式
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)

    # 添加处理器到根日志记录器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # 配置特定模块的日志级别
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    app.logger.info('日志系统初始化完成')

def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    return logging.getLogger(name)