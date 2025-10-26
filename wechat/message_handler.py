"""
微信消息处理器
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from services.news_service import NewsService
from wechat.formatter import FormatterFactory, WechatTextFormatter, NewsGroupFormatter
from utils.logger import get_logger

logger = get_logger(__name__)

class WeChatMessageHandler:
    """微信消息处理器"""

    def __init__(self):
        self.news_service = NewsService()
        self.formatter = WechatTextFormatter()
        self.group_formatter = NewsGroupFormatter()

        # 定义关键词映射
        self.keyword_mappings = {
            # 新闻类型
            '科技': {'category': 'tech', 'action': 'category_news'},
            'AI': {'category': 'ai', 'action': 'category_news'},
            '人工智能': {'category': 'ai', 'action': 'category_news'},
            '技术': {'category': 'tech', 'action': 'category_news'},

            # 功能关键词
            '今日': {'action': 'today_news'},
            '今天': {'action': 'today_news'},
            '最新': {'action': 'recent_news'},
            '热门': {'action': 'hot_news'},
            '帮助': {'action': 'help'},
            '功能': {'action': 'help'},
            '菜单': {'action': 'help'},
            '分类': {'action': 'categories'},
            '统计': {'action': 'statistics'},
            '摘要': {'action': 'summary'},
            '排行': {'action': 'hot_news'},
            '搜索': {'action': 'search'},
            '找': {'action': 'search'},
        }

        # 帮助信息
        self.help_message = (
            "📱 RSS新闻机器人 📱\n\n"
            "🔍 功能菜单:\n"
            "• 输入「今日」或「今天」- 查看今日新闻\n"
            "• 输入「科技」- 查看科技类新闻\n"
            "• 输入「AI」或「人工智能」- 查看AI类新闻\n"
            "• 输入「热门」或「排行」- 查看热门新闻\n"
            "• 输入「分类」- 查看所有新闻分类\n"
            "• 输入「统计」- 查看新闻统计信息\n"
            "• 输入「摘要」- 查看今日新闻摘要\n"
            "• 输入「搜索+关键词」- 搜索新闻\n"
            "• 输入「帮助」- 显示此帮助信息\n\n"
            "💡 小提示:\n"
            "• 可以直接输入关键词搜索新闻\n"
            "• 系统每天早上5点自动更新新闻\n"
            "• 只保留最近7天的新闻数据\n\n"
            "📊 数据来源: 36氪、虎嗅网、机器之心等"
        )

    def handle_message(self, message: Dict[str, Any]) -> str:
        """处理微信消息"""
        try:
            # 提取消息内容
            content = self._extract_message_content(message)
            if not content:
                return self._format_error_message("消息内容为空")

            logger.info(f"收到用户消息: {content}")

            # 解析用户意图
            intent = self._parse_user_intent(content)

            # 处理消息
            response = self._process_intent(intent, content)

            logger.info(f"回复用户消息: {response[:100]}...")
            return response

        except Exception as e:
            logger.error(f"处理微信消息失败: {e}")
            return self._format_error_message("系统繁忙，请稍后再试")

    def _extract_message_content(self, message: Dict[str, Any]) -> str:
        """提取消息内容"""
        # 支持多种消息格式
        content = None

        if 'Content' in message:
            content = message['Content']
        elif 'content' in message:
            content = message['content']
        elif 'text' in message:
            content = message['text']

        if content:
            return content.strip()

        return None

    def _parse_user_intent(self, content: str) -> Dict[str, Any]:
        """解析用户意图"""
        content_lower = content.lower().strip()

        # 检查是否为搜索指令
        if content_lower.startswith(('搜索', '找')):
            return {
                'action': 'search',
                'keyword': content[2:].strip() if len(content) > 2 else ''
            }

        # 检查是否为日期查询
        date_patterns = {
            r'昨天': datetime.utcnow() - timedelta(days=1),
            r'前天': datetime.utcnow() - timedelta(days=2),
            r'(\d{4}-\d{1,2}-\d{1,2})': None,  # 具体日期格式
        }

        for pattern, date_obj in date_patterns.items():
            if re.search(pattern, content_lower):
                if pattern.startswith('('):  # 具体日期
                    match = re.search(pattern, content_lower)
                    if match:
                        try:
                            date_obj = datetime.strptime(match.group(1), '%Y-%m-%d')
                        except ValueError:
                            continue

                return {
                    'action': 'date_news',
                    'date': date_obj.date() if date_obj else None
                }

        # 检查关键词映射
        for keyword, mapping in self.keyword_mappings.items():
            if keyword in content:
                return mapping

        # 默认意图：搜索或今日新闻
        if len(content) >= 2:  # 如果内容较长，可能是搜索
            return {
                'action': 'search',
                'keyword': content
            }
        else:  # 否则显示今日新闻
            return {'action': 'today_news'}

    def _process_intent(self, intent: Dict[str, Any], original_content: str) -> str:
        """处理用户意图"""
        action = intent.get('action', 'today_news')

        try:
            if action == 'today_news':
                return self._handle_today_news(intent)
            elif action == 'category_news':
                return self._handle_category_news(intent)
            elif action == 'recent_news':
                return self._handle_recent_news(intent)
            elif action == 'hot_news':
                return self._handle_hot_news(intent)
            elif action == 'search':
                return self._handle_search_news(intent)
            elif action == 'date_news':
                return self._handle_date_news(intent)
            elif action == 'categories':
                return self._handle_categories()
            elif action == 'statistics':
                return self._handle_statistics()
            elif action == 'summary':
                return self._handle_summary()
            elif action == 'help':
                return self.help_message
            else:
                return self._handle_today_news(intent)

        except Exception as e:
            logger.error(f"处理意图失败: {action}, 错误: {e}")
            return self._format_error_message("处理请求失败，请稍后再试")

    def _handle_today_news(self, intent: Dict[str, Any]) -> str:
        """处理今日新闻请求"""
        category = intent.get('category')

        if category:
            news_list = self.news_service.get_today_news(category=category, limit=8)
            return self.formatter.format(news_list, category=category)
        else:
            news_list = self.news_service.get_today_news(limit=10)
            return self.formatter.format(news_list)

    def _handle_category_news(self, intent: Dict[str, Any]) -> str:
        """处理分类新闻请求"""
        category = intent.get('category')
        if not category:
            return self._format_error_message("请指定新闻分类")

        news_list = self.news_service.get_recent_news(days=3, category=category, limit=8)
        return self.formatter.format(news_list, category=category)

    def _handle_recent_news(self, intent: Dict[str, Any]) -> str:
        """处理最新新闻请求"""
        news_list = self.news_service.get_recent_news(days=3, limit=10)
        return self.formatter.format(news_list)

    def _handle_hot_news(self, intent: Dict[str, Any]) -> str:
        """处理热门新闻请求"""
        hot_news = self.news_service.get_hot_news(days=3, limit=5)
        return self.group_formatter.format_hot_news(hot_news)

    def _handle_search_news(self, intent: Dict[str, Any]) -> str:
        """处理新闻搜索请求"""
        keyword = intent.get('keyword', '').strip()
        if not keyword:
            return self._format_error_message("请输入搜索关键词")

        news_list = self.news_service.search_news(keyword, limit=8)

        if news_list:
            return self.formatter.format(news_list,
                                       title=f"搜索结果: {keyword} (找到{len(news_list)}条)")
        else:
            return f"🔍 搜索「{keyword}」\n\n未找到相关新闻，请尝试其他关键词。\n\n💡 输入「帮助」查看更多功能"

    def _handle_date_news(self, intent: Dict[str, Any]) -> str:
        """处理日期新闻请求"""
        date = intent.get('date')
        if not date:
            return self._format_error_message("日期格式不正确")

        news_list = self.news_service.get_news_by_date(date, limit=8)
        return self.formatter.format(news_list, date=date)

    def _handle_categories(self) -> str:
        """处理分类列表请求"""
        categories = self.news_service.get_news_categories()

        if not categories:
            return "📂 暂无新闻分类"

        content = "📂 新闻分类 📂\n\n"
        for i, category in enumerate(categories, 1):
            content += f"{i}. {category}\n"

        content += "\n💡 直接输入分类名称查看该类新闻"
        return content

    def _handle_statistics(self) -> str:
        """处理统计信息请求"""
        stats = self.news_service.get_news_statistics()

        content = "📊 新闻统计 📊\n\n"
        content += f"📰 总新闻数: {stats.get('total_news', 0)}条\n"
        content += f"📅 今日新闻: {stats.get('today_news', 0)}条\n"
        content += f"📈 本周新闻: {stats.get('week_news', 0)}条\n"
        content += f"📉 本月新闻: {stats.get('month_news', 0)}条\n"

        category_stats = stats.get('category_stats', {})
        if category_stats:
            content += "\n📂 分类统计:\n"
            for category, count in category_stats.items():
                content += f"• {category}: {count}条\n"

        content += f"\n⏰ 统计时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return content

    def _handle_summary(self) -> str:
        """处理新闻摘要请求"""
        today_news = self.news_service.get_today_news(limit=20)
        return self.group_formatter.format_by_category(today_news)

    def _format_error_message(self, message: str) -> str:
        """格式化错误消息"""
        return f"❌ {message}\n\n💡 输入「帮助」查看可用功能"

    def get_command_list(self) -> List[Dict[str, str]]:
        """获取命令列表"""
        return [
            {'command': '今日/今天', 'description': '查看今日新闻'},
            {'command': '科技', 'description': '查看科技类新闻'},
            {'command': 'AI/人工智能', 'description': '查看AI类新闻'},
            {'command': '热门/排行', 'description': '查看热门新闻'},
            {'command': '分类', 'description': '查看所有分类'},
            {'command': '统计', 'description': '查看统计信息'},
            {'command': '摘要', 'description': '查看新闻摘要'},
            {'command': '搜索+关键词', 'description': '搜索新闻'},
            {'command': '帮助', 'description': '显示帮助信息'},
        ]

    def is_command_message(self, content: str) -> bool:
        """判断是否为命令消息"""
        content_lower = content.lower().strip()

        # 检查是否为已知命令
        for keyword in self.keyword_mappings.keys():
            if keyword in content_lower:
                return True

        # 检查是否为搜索命令
        if content_lower.startswith(('搜索', '找')):
            return True

        # 检查是否为日期查询
        date_keywords = ['昨天', '前天']
        for keyword in date_keywords:
            if keyword in content_lower:
                return True

        # 检查是否为日期格式
        if re.match(r'\d{4}-\d{1,2}-\d{1,2}', content_lower):
            return True

        return False