"""
微信公众号API接口
"""

import hashlib
import xml.etree.ElementTree as ET
from flask import Blueprint, request, jsonify, current_app, make_response
from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature

from wechat.message_handler import WeChatMessageHandler
from utils.logger import get_logger

logger = get_logger(__name__)

# 创建蓝图
wechat_bp = Blueprint('wechat', __name__)

# 创建消息处理器
message_handler = WeChatMessageHandler()

@wechat_bp.route('/message', methods=['GET', 'POST'])
def wechat_message():
    """微信公众号消息接口"""
    try:
        # 验证请求签名
        if not _verify_signature():
            logger.warning("微信公众号请求签名验证失败")
            return "Invalid signature", 403

        # 处理验证请求
        if request.method == 'GET':
            return _handle_verification()

        # 处理消息
        if request.method == 'POST':
            return _handle_message()

    except Exception as e:
        logger.error(f"处理微信消息接口异常: {e}")
        return jsonify({
            'error': True,
            'message': 'Internal Server Error'
        }), 500

def _verify_signature() -> bool:
    """验证微信服务器签名"""
    try:
        # 获取微信服务器发送的参数
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')

        # 获取配置的token
        token = current_app.config.get('WECHAT_TOKEN')
        if not token:
            logger.error("微信Token未配置")
            return False

        # 使用wechatpy验证签名
        wechat_signature = WeChatSignature(token)
        return wechat_signature.check(signature, timestamp, nonce)

    except Exception as e:
        logger.error(f"签名验证异常: {e}")
        return False

def _handle_verification():
    """处理服务器验证请求"""
    try:
        echostr = request.args.get('echostr', '')
        if echostr:
            logger.info("微信公众号服务器验证成功")
            return echostr
        else:
            logger.warning("微信验证请求缺少echostr参数")
            return "Missing echostr", 400

    except Exception as e:
        logger.error(f"处理微信验证请求异常: {e}")
        return "Verification failed", 500

def _handle_message():
    """处理微信消息"""
    try:
        # 获取XML消息内容
        xml_data = request.data.decode('utf-8')
        if not xml_data:
            logger.warning("收到空消息")
            return "Empty message", 400

        logger.debug(f"收到微信消息: {xml_data}")

        # 解析消息
        message = parse_message(xml_data)

        # 记录消息信息
        logger.info(f"收到{message.type}消息: from={message.source}, to={message.target}, content={message.content if hasattr(message, 'content') else ''}")

        # 处理消息并生成回复
        response = _process_message(message)

        # 返回XML响应
        response_xml = response.render()

        logger.debug(f"回复微信消息: {response_xml}")
        return response_xml, 200, {'Content-Type': 'application/xml'}

    except Exception as e:
        logger.error(f"处理微信消息异常: {e}")
        # 返回错误回复
        return _create_error_reply()

def _process_message(message) -> create_reply:
    """处理消息并生成回复"""
    try:
        # 只处理文本消息
        if message.type != 'text':
            logger.info(f"收到非文本消息类型: {message.type}")
            return _create_help_reply(message.source)

        # 获取消息内容
        if not hasattr(message, 'content') or not message.content:
            logger.warning("文本消息无内容")
            return _create_help_reply(message.source)

        content = message.content.strip()
        logger.info(f"处理文本消息: {content}")

        # 处理消息
        response_text = message_handler.handle_message({'Content': content})

        # 创建回复
        reply = create_reply(response_text, message)
        return reply

    except Exception as e:
        logger.error(f"处理消息异常: {e}")
        return _create_error_reply(message.source)

def _create_help_reply(user_id: str) -> create_reply:
    """创建帮助回复"""
    help_text = message_handler.help_message
    reply = create_reply(help_text, create_reply(user_id))
    return reply

def _create_error_reply(user_id: str = None) -> create_reply:
    """创建错误回复"""
    error_text = "❌ 系统繁忙，请稍后再试\n\n💡 输入「帮助」查看可用功能"

    if user_id:
        from wechatpy.replies import TextReply
        return TextReply(error_text, user_id)
    else:
        return create_reply(error_text)

@wechat_bp.route('/test', methods=['GET'])
def test_api():
    """测试接口"""
    return jsonify({
        'status': 'ok',
        'message': '微信公众号API运行正常',
        'timestamp': request.args.get('timestamp', '')
    })

@wechat_bp.route('/config', methods=['GET'])
def get_config():
    """获取配置信息（用于调试）"""
    try:
        # 只返回非敏感配置
        config_info = {
            'app_name': current_app.name,
            'environment': current_app.config.get('FLASK_ENV', 'unknown'),
            'news_retention_days': current_app.config.get('NEWS_RETENTION_DAYS', 7),
            'rss_collect_hour': current_app.config.get('RSS_COLLECT_HOUR', 5),
            'supported_commands': message_handler.get_command_list()
        }

        return jsonify(config_info)

    except Exception as e:
        logger.error(f"获取配置信息异常: {e}")
        return jsonify({'error': str(e)}), 500

@wechat_bp.route('/webhook/test', methods=['POST'])
def test_webhook():
    """测试Webhook（用于测试消息处理）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing JSON data'}), 400

        # 模拟处理消息
        if 'message' in data:
            response_text = message_handler.handle_message(data['message'])
            return jsonify({
                'success': True,
                'response': response_text,
                'message_type': 'text'
            })

        return jsonify({'error': 'Missing message field'}), 400

    except Exception as e:
        logger.error(f"测试Webhook异常: {e}")
        return jsonify({'error': str(e)}), 500

@wechat_bp.before_request
def log_request():
    """记录请求信息"""
    if request.endpoint and 'wechat' in request.endpoint:
        logger.info(f"收到微信请求: {request.method} {request.path}, IP: {request.remote_addr}")

@wechat_bp.after_request
def log_response(response):
    """记录响应信息"""
    if request.endpoint and 'wechat' in request.endpoint:
        logger.info(f"微信请求响应: 状态码 {response.status_code}")
    return response

# 错误处理器
@wechat_bp.errorhandler(400)
def bad_request(error):
    """处理400错误"""
    logger.warning(f"微信请求400错误: {error.description}")
    return jsonify({'error': 'Bad Request'}), 400

@wechat_bp.errorhandler(403)
def forbidden(error):
    """处理403错误"""
    logger.warning(f"微信请求403错误: 签名验证失败")
    return jsonify({'error': 'Forbidden'}), 403

@wechat_bp.errorhandler(404)
def not_found(error):
    """处理404错误"""
    logger.warning(f"微信请求404错误: {request.path}")
    return jsonify({'error': 'Not Found'}), 404

@wechat_bp.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    logger.error(f"微信请求500错误: {error}")
    return jsonify({'error': 'Internal Server Error'}), 500