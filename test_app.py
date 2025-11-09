"""
Flask应用测试
"""
import unittest
import json
from unittest.mock import Mock, patch
from datetime import datetime
from test_framework import BaseTestCase
from app import app, create_app, WeChatNewsBot
from models import db_manager, News
from logger_config import app_logger


class TestFlaskApp(BaseTestCase):
    """Flask应用测试"""

    def setUp(self):
        """测试初始化"""
        super().setUp()
        # 创建测试客户端
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        """测试清理"""
        super().tearDown()
        self.app_context.pop()

    def test_health_check_success(self):
        """测试健康检查成功"""
        response = self.client.get('/health')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('database', data)
        self.assertIn('news_count', data)

    def test_health_check_failure(self):
        """测试健康检查失败"""
        with patch.object(db_manager, 'get_news_count', side_effect=Exception("Database error")):
            response = self.client.get('/health')

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'unhealthy')
            self.assertIn('error', data)

    def test_get_news_success(self):
        """测试获取新闻成功"""
        # 创建测试新闻
        news1 = self.create_test_news(
            title='新闻1',
            url='https://example.com/news1',
            category='tech'
        )
        news2 = self.create_test_news(
            title='新闻2',
            url='https://example.com/news2',
            category='ai'
        )

        response = self.client.get('/news')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['news']), 2)

    def test_get_news_with_category(self):
        """测试按分类获取新闻"""
        # 创建不同分类的新闻
        tech_news = self.create_test_news(
            title='科技新闻',
            url='https://example.com/tech',
            category='tech'
        )
        ai_news = self.create_test_news(
            title='AI新闻',
            url='https://example.com/ai',
            category='ai'
        )

        # 获取科技类新闻
        response = self.client.get('/news?category=tech')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['news'][0]['category'], 'tech')

    def test_get_news_with_limit(self):
        """测试限制获取新闻数量"""
        # 创建多条新闻
        for i in range(5):
            self.create_test_news(
                title=f'新闻{i}',
                url=f'https://example.com/news{i}'
            )

        response = self.client.get('/news?limit=3')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(data['news']), 3)

    def test_collect_news_success(self):
        """测试手动触发新闻收集成功"""
        with patch('app.rss_collector.collect_all_news', return_value=5) as mock_collect:
            response = self.client.post('/collect_news')

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'success')
            self.assertEqual(data['collected_count'], 5)
            mock_collect.assert_called_once()

    def test_collect_news_failure(self):
        """测试手动触发新闻收集失败"""
        with patch('app.rss_collector.collect_all_news', side_effect=Exception("Collection error")):
            response = self.client.post('/collect_news')

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'error')
            self.assertIn('error', data)

    def test_wechat_get_verification_success(self):
        """测试微信服务器验证成功"""
        # 模拟微信验证参数
        params = {
            'signature': 'valid_signature',
            'timestamp': '1234567890',
            'nonce': '123456',
            'echostr': 'test_echostr'
        }

        with patch('app.check_signature', return_value=True):
            response = self.client.get('/wechat', query_string=params)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data.decode(), 'test_echostr')

    def test_wechat_get_verification_failure(self):
        """测试微信服务器验证失败"""
        params = {
            'signature': 'invalid_signature',
            'timestamp': '1234567890',
            'nonce': '123456',
            'echostr': 'test_echostr'
        }

        with patch('app.check_signature', side_effect=Exception("Invalid signature")):
            response = self.client.get('/wechat', query_string=params)

            self.assertEqual(response.status_code, 403)

    def test_wechat_post_text_message(self):
        """测试微信POST文本消息"""
        # 创建测试新闻
        test_news = self.create_test_news(
            title='测试新闻标题',
            content='测试新闻内容',
            url='https://example.com/test',
            source='测试来源',
            category='tech'
        )

        # 模拟微信消息
        xml_data = """
        <xml>
            <ToUserName><![CDATA[toUser]]></ToUserName>
            <FromUserName><![CDATA[fromUser]]></FromUserName>
            <CreateTime>1234567890</CreateTime>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA[新闻]]></Content>
            <MsgId>1234567890123456</MsgId>
        </xml>
        """

        with patch('app.parse_message') as mock_parse, \
             patch('app.create_reply') as mock_create_reply:

            # 模拟解析消息
            mock_message = Mock()
            mock_message.type = 'text'
            mock_message.source = 'fromUser'
            mock_message.content = '新闻'
            mock_parse.return_value = mock_message

            # 模拟创建回复
            mock_reply = Mock()
            mock_reply.render.return_value = 'mock_reply_xml'
            mock_create_reply.return_value = mock_reply

            response = self.client.post(
                '/wechat',
                data=xml_data,
                content_type='text/xml'
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/xml')
            self.assertIn('mock_reply_xml', response.data.decode())

    def test_wechat_post_non_text_message(self):
        """测试微信POST非文本消息"""
        xml_data = """
        <xml>
            <ToUserName><![CDATA[toUser]]></ToUserName>
            <FromUserName><![CDATA[fromUser]]></FromUserName>
            <CreateTime>1234567890</CreateTime>
            <MsgType><![CDATA[image]]></MsgType>
            <PicUrl><![CDATA[http://example.com/image.jpg]]></PicUrl>
            <MediaId><![CDATA[media_id]]></MediaId>
            <MsgId>1234567890123456</MsgId>
        </xml>
        """

        with patch('app.parse_message') as mock_parse, \
             patch('app.create_reply') as mock_create_reply:

            # 模拟解析消息
            mock_message = Mock()
            mock_message.type = 'image'
            mock_message.source = 'fromUser'
            mock_parse.return_value = mock_message

            # 模拟创建回复
            mock_reply = Mock()
            mock_reply.render.return_value = 'mock_image_reply_xml'
            mock_create_reply.return_value = mock_reply

            response = self.client.post(
                '/wechat',
                data=xml_data,
                content_type='text/xml'
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/xml')

    def test_404_error_handler(self):
        """测试404错误处理"""
        response = self.client.get('/nonexistent')

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Not found')


class TestWeChatNewsBot(BaseTestCase):
    """微信新闻机器人测试"""

    def setUp(self):
        """测试初始化"""
        super().setUp()
        self.bot = WeChatNewsBot()

    def test_format_news_message_with_news(self):
        """测试有新闻时的消息格式化"""
        # 创建测试新闻
        tech_news = self.create_test_news(
            title='科技新闻标题',
            content='科技新闻内容',
            url='https://example.com/tech',
            source='TechNews',
            category='tech'
        )
        ai_news = self.create_test_news(
            title='AI新闻标题',
            content='AI新闻内容',
            url='https://example.com/ai',
            source='AINews',
            category='ai'
        )

        news_list = [tech_news, ai_news]
        message = self.bot.format_news_message(news_list)

        # 验证消息包含必要信息
        self.assertIn('科技/AI新闻速递', message)
        self.assertIn('科技新闻', message)
        self.assertIn('AI新闻', message)
        self.assertIn('科技新闻标题', message)
        self.assertIn('AI新闻标题', message)
        self.assertIn('https://example.com/tech', message)
        self.assertIn('https://example.com/ai', message)

    def test_format_news_message_empty(self):
        """测试无新闻时的消息格式化"""
        message = self.bot.format_news_message([])

        self.assertIn('今日暂无科技/AI新闻更新', message)

    def test_handle_text_message_success(self):
        """测试处理文本消息成功"""
        # 创建测试新闻
        test_news = self.create_test_news(
            title='测试新闻',
            content='测试内容',
            url='https://example.com/test',
            source='TestNews',
            category='tech'
        )

        # 模拟微信消息
        mock_message = Mock()
        mock_message.type = 'text'
        mock_message.source = 'test_user'
        mock_message.content = '获取新闻'

        with patch('app.create_reply') as mock_create_reply:
            mock_reply = Mock()
            mock_create_reply.return_value = mock_reply

            reply = self.bot.handle_text_message(mock_message)

            self.assertIsNotNone(reply)
            mock_create_reply.assert_called_once()

    def test_handle_text_message_no_news(self):
        """测试处理文本消息但无新闻"""
        mock_message = Mock()
        mock_message.type = 'text'
        mock_message.source = 'test_user'
        mock_message.content = '获取新闻'

        with patch('app.create_reply') as mock_create_reply:
            mock_reply = Mock()
            mock_create_reply.return_value = mock_reply

            reply = self.bot.handle_text_message(mock_message)

            self.assertIsNotNone(reply)
            mock_create_reply.assert_called_once()

    def test_handle_text_message_exception(self):
        """测试处理文本消息异常"""
        mock_message = Mock()
        mock_message.type = 'text'
        mock_message.source = 'test_user'
        mock_message.content = '获取新闻'

        with patch.object(db_manager, 'get_today_news', side_effect=Exception("Database error")), \
             patch('app.create_reply') as mock_create_reply:

            mock_reply = Mock()
            mock_create_reply.return_value = mock_reply

            reply = self.bot.handle_text_message(mock_message)

            self.assertIsNotNone(reply)
            # 应该调用错误回复
            mock_create_reply.assert_called_once()

    def test_handle_other_message(self):
        """测试处理其他类型消息"""
        mock_message = Mock()
        mock_message.type = 'image'
        mock_message.source = 'test_user'

        with patch('app.create_reply') as mock_create_reply:
            mock_reply = Mock()
            mock_create_reply.return_value = mock_reply

            reply = self.bot.handle_other_message(mock_message)

            self.assertIsNotNone(reply)
            mock_create_reply.assert_called_once()


if __name__ == '__main__':
    unittest.main()