"""
Flask主应用 - 微信公众号RSS新闻机器人
"""
import os
import hashlib
from flask import Flask, request, abort, make_response
from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException
from datetime import datetime
from models import db_manager
from rss_collector import rss_collector
from logger_config import app_logger
from config import Config, config_map


def create_app(config_name='default'):
    """创建Flask应用实例"""
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config_map[config_name])

    # 初始化数据库
    try:
        db_manager.init_db()
    except Exception as e:
        app_logger.error(f"数据库初始化失败: {e}")

    return app


# 创建应用实例
app = create_app(os.getenv('FLASK_ENV', 'default'))


class WeChatNewsBot:
    """微信公众号新闻机器人"""

    def __init__(self):
        self.app_id = Config.WECHAT_APP_ID
        self.app_secret = Config.WECHAT_APP_SECRET
        self.token = Config.WECHAT_TOKEN

    def format_news_message(self, news_list):
        """格式化新闻消息"""
        if not news_list:
            return "📰 今日暂无科技/AI新闻更新，请稍后再试。"

        # 按分类组织新闻
        tech_news = [news for news in news_list if news.category == 'tech']
        ai_news = [news for news in news_list if news.category == 'ai']

        messages = []
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 消息头部
        messages.append(f"📱 **科技/AI新闻速递** 📱")
        messages.append(f"📅 {datetime.now().strftime('%Y年%m月%d日')}")
        messages.append(f"⏰ 更新时间: {current_time}")
        messages.append("─" * 30)

        # 科技新闻
        if tech_news:
            messages.append("\n🔬 **科技新闻**")
            for i, news in enumerate(tech_news[:5], 1):  # 最多显示5条
                messages.append(f"\n{i}. 📰 {news.title}")
                if news.content:
                    content = news.content[:100] + "..." if len(news.content) > 100 else news.content
                    messages.append(f"   📝 {content}")
                messages.append(f"   🔗 {news.url}")
                messages.append(f"   📤 来源: {news.source}")

        # AI新闻
        if ai_news:
            messages.append("\n🤖 **AI新闻**")
            for i, news in enumerate(ai_news[:5], 1):  # 最多显示5条
                messages.append(f"\n{i}. 📰 {news.title}")
                if news.content:
                    content = news.content[:100] + "..." if len(news.content) > 100 else news.content
                    messages.append(f"   📝 {content}")
                messages.append(f"   🔗 {news.url}")
                messages.append(f"   📤 来源: {news.source}")

        # 消息尾部
        messages.append("\n" + "─" * 30)
        messages.append("💡 发送任意文字获取最新新闻")
        messages.append("🔔 本消息每日自动更新")

        return "\n".join(messages)

    def handle_text_message(self, message):
        """处理文本消息"""
        try:
            app_logger.info(f"收到用户消息: {message.content} (from {message.source})")

            # 获取今日新闻
            news_list = db_manager.get_today_news(limit=Config.MAX_NEWS_PER_REPLY)

            # 格式化回复内容
            reply_content = self.format_news_message(news_list)

            # 创建回复
            reply = create_reply(reply_content, message)
            app_logger.info(f"发送回复给用户 {message.source}")

            return reply

        except Exception as e:
            app_logger.error(f"处理文本消息失败: {e}")
            error_reply = create_reply("抱歉，系统繁忙，请稍后再试。", message)
            return error_reply

    def handle_other_message(self, message):
        """处理其他类型消息"""
        app_logger.info(f"收到非文本消息: {message.type} (from {message.source})")

        reply_text = (
            "📰 您好！我是科技/AI新闻机器人\n\n"
            "🔸 发送任意文字获取今日科技/AI新闻\n"
            "🔸 新闻每日自动更新\n"
            "🔸 支持科技和AI两大分类\n\n"
            "💡 现在就试试吧！"
        )

        return create_reply(reply_text, message)


# 创建机器人实例
bot = WeChatNewsBot()


@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    """微信公众号入口"""
    try:
        # 验证服务器配置
        if request.method == 'GET':
            signature = request.args.get('signature', '')
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            echostr = request.args.get('echostr', '')

            try:
                check_signature(Config.WECHAT_TOKEN, signature, timestamp, nonce)
                app_logger.info("微信服务器验证成功")
                return echostr
            except InvalidSignatureException:
                app_logger.error("微信服务器验证失败")
                abort(403)

        # 处理消息
        elif request.method == 'POST':
            # 解析消息
            try:
                message = parse_message(request.data)
                app_logger.debug(f"收到微信消息: {message.type} from {message.source}")
            except Exception as e:
                app_logger.error(f"解析微信消息失败: {e}")
                abort(400)

            # 根据消息类型处理
            if message.type == 'text':
                reply = bot.handle_text_message(message)
            else:
                reply = bot.handle_other_message(message)

            # 返回回复
            response = make_response(reply.render())
            response.content_type = 'application/xml'
            return response

    except Exception as e:
        app_logger.error(f"微信接口处理异常: {e}")
        abort(500)


@app.route('/health')
def health_check():
    """健康检查接口"""
    try:
        # 检查数据库连接
        news_count = db_manager.get_news_count()

        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'news_count': news_count
        }
    except Exception as e:
        app_logger.error(f"健康检查失败: {e}")
        return {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }, 500


@app.route('/collect_news', methods=['POST'])
def trigger_news_collection():
    """手动触发新闻收集"""
    try:
        app_logger.info("手动触发新闻收集")
        count = rss_collector.collect_all_news()
        return {
            'status': 'success',
            'collected_count': count,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        app_logger.error(f"手动触发新闻收集失败: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500


@app.route('/news')
def get_news():
    """获取新闻API"""
    try:
        category = request.args.get('category')
        limit = request.args.get('limit', 20, type=int)

        news_list = db_manager.get_today_news(category=category, limit=limit)

        return {
            'status': 'success',
            'count': len(news_list),
            'news': [news.to_dict() for news in news_list]
        }
    except Exception as e:
        app_logger.error(f"获取新闻失败: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }, 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return {'error': 'Not found'}, 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    app_logger.error(f"内部服务器错误: {error}")
    return {'error': 'Internal server error'}, 500


if __name__ == '__main__':
    app_logger.info("启动微信公众号RSS新闻机器人...")

    # 验证必要配置
    try:
        Config.validate_config()
    except ValueError as e:
        app_logger.error(f"配置验证失败: {e}")
        exit(1)

    # 启动Flask应用
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )