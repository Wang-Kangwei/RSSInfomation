"""
Flask应用工厂
"""

import os
from flask import Flask
from flask_cors import CORS

from core.database import db, init_db
from config.settings import config
from utils.logger import setup_logging

def create_app(config_name=None):
    """创建Flask应用实例"""

    # 确定配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    # 创建Flask应用
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config[config_name])

    # 设置日志
    setup_logging(app)

    # 初始化扩展
    _init_extensions(app)

    # 注册蓝图
    _register_blueprints(app)

    # 注册错误处理器
    _register_error_handlers(app)

    # 注册CLI命令
    _register_cli_commands(app)

    # 注册模板上下文
    _register_template_context(app)

    return app

def _init_extensions(app):
    """初始化Flask扩展"""

    # 初始化数据库
    db.init_app(app)

    # 配置CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

def _register_blueprints(app):
    """注册蓝图"""

    # 导入并注册微信API蓝图
    from wechat.api import wechat_bp
    app.register_blueprint(wechat_bp, url_prefix='/wechat')

    # 导入并注册管理API蓝图 (可选)
    try:
        from wechat.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
    except ImportError:
        pass  # 管理模块是可选的

def _register_error_handlers(app):
    """注册错误处理器"""

    from core.exceptions import RSSInfomationError
    from flask import jsonify, request

    @app.errorhandler(RSSInfomationError)
    def handle_rss_information_error(error):
        """处理RSSInfomation自定义异常"""
        response = {
            'error': True,
            'message': error.message,
            'error_code': error.error_code
        }

        # 如果是API请求，返回JSON格式
        if request.path.startswith('/api/') or request.path.startswith('/wechat/'):
            return jsonify(response), 400

        # 否则返回错误页面
        return response, 400

    @app.errorhandler(404)
    def handle_not_found(error):
        """处理404错误"""
        response = {
            'error': True,
            'message': '请求的资源不存在',
            'error_code': 'NOT_FOUND'
        }

        if request.path.startswith('/api/') or request.path.startswith('/wechat/'):
            return jsonify(response), 404

        return response, 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        """处理500错误"""
        response = {
            'error': True,
            'message': '服务器内部错误',
            'error_code': 'INTERNAL_ERROR'
        }

        if request.path.startswith('/api/') or request.path.startswith('/wechat/'):
            return jsonify(response), 500

        return response, 500

def _register_cli_commands(app):
    """注册CLI命令"""

    @app.cli.command()
    def init_db():
        """初始化数据库"""
        init_db()
        print('数据库初始化完成')

    @app.cli.command()
    def create_tables():
        """创建数据库表"""
        db.create_all()
        print('数据库表创建完成')

    @app.cli.command()
    def reset_db():
        """重置数据库"""
        db.drop_all()
        db.create_all()
        init_db()
        print('数据库重置完成')

def _register_template_context(app):
    """注册模板上下文处理器"""

    @app.context_processor
    def inject_config():
        """向模板注入配置信息"""
        return {
            'app_name': 'RSSInfomation',
            'version': '1.0.0'
        }