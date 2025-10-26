"""
微信消息格式化器
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

from models.news import News
from utils.helpers import clean_text, truncate_text, format_date, time_ago

class MessageFormatter(ABC):
    """消息格式化器抽象基类"""

    @abstractmethod
    def format(self, news_items: List[News], **kwargs) -> str:
        """格式化新闻列表"""
        pass

class WechatTextFormatter(MessageFormatter):
    """微信文本消息格式化器"""

    def __init__(self):
        self.max_items_per_message = 8  # 每条消息最多显示8条新闻
        self.max_title_length = 50     # 标题最大长度

    def format(self, news_items: List[News], **kwargs) -> str:
        """格式化新闻为微信文本消息"""
        if not news_items:
            return self._format_empty_message(**kwargs)

        # 根据分类或日期分组
        category = kwargs.get('category')
        date = kwargs.get('date')

        # 构建消息头部
        header = self._build_header(category, date, len(news_items))

        # 构建新闻列表
        news_content = self._build_news_list(news_items)

        # 构建消息尾部
        footer = self._build_footer()

        return f"{header}\n\n{news_content}\n\n{footer}"

    def format_news_item(self, news: News, index: int = 0) -> str:
        """格式化单条新闻"""
        # 处理标题
        title = clean_text(news.title)
        if len(title) > self.max_title_length:
            title = truncate_text(title, self.max_title_length)

        # 构建新闻项
        news_item = f"{index}. 【{title}】"

        # 添加来源和时间
        source_info = f"📰 {news.source_name}"
        if news.pub_date:
            time_info = time_ago(news.pub_date)
            source_info += f" • {time_info}"

        news_item += f"\n   {source_info}"

        return news_item

    def _build_header(self, category: str = None, date: datetime = None, count: int = 0) -> str:
        """构建消息头部"""
        if category:
            title = f"【{category}类新闻】"
        else:
            title = "【今日科技新闻】"

        if date:
            date_str = format_date(date)
            subtitle = f"{date_str} 共收集到 {count} 条新闻"
        else:
            subtitle = f"共收集到 {count} 条新闻"

        return f"{title}\n{subtitle}"

    def _build_news_list(self, news_items: List[News]) -> str:
        """构建新闻列表"""
        news_lines = []

        # 限制显示数量
        display_items = news_items[:self.max_items_per_message]

        for i, news in enumerate(display_items, 1):
            news_item = self.format_news_item(news, i)
            news_lines.append(news_item)

        # 如果有更多新闻，添加提示
        if len(news_items) > self.max_items_per_message:
            remaining = len(news_items) - self.max_items_per_message
            news_lines.append(f"\n... 还有 {remaining} 条新闻")

        return "\n\n".join(news_lines)

    def _build_footer(self) -> str:
        """构建消息尾部"""
        return (
            "💡 输入「科技」查看科技类新闻\n"
            "💡 输入「AI」查看AI类新闻\n"
            "💡 输入「帮助」查看更多功能"
        )

    def _format_empty_message(self, **kwargs) -> str:
        """格式化空消息"""
        category = kwargs.get('category')
        date = kwargs.get('date')

        if category:
            title = f"【{category}类新闻】"
        else:
            title = "【今日新闻】"

        if date:
            date_str = format_date(date)
            message = f"{title}\n{date_str}\n\n暂无相关新闻，请稍后再试 📱"
        else:
            message = f"{title}\n\n今日暂无新闻更新，请稍后再试 📱"

        message += "\n\n💡 输入「帮助」查看更多功能"

        return message

class MarkdownFormatter(MessageFormatter):
    """Markdown格式化器"""

    def format(self, news_items: List[News], **kwargs) -> str:
        """格式化新闻为Markdown格式"""
        if not news_items:
            return "# 今日新闻\n\n暂无新闻更新。"

        # 构建Markdown内容
        content = "# 今日新闻\n\n"

        for i, news in enumerate(news_items, 1):
            content += f"## {i}. {news.title}\n\n"

            content += f"**来源**: {news.source_name}\n"
            content += f"**链接**: [查看原文]({news.link})\n"

            if news.pub_date:
                content += f"**发布时间**: {format_date(news.pub_date)}\n"

            content += f"**收集时间**: {format_date(news.collect_time)}\n\n"
            content += "---\n\n"

        return content

class SummaryFormatter(MessageFormatter):
    """摘要格式化器"""

    def format(self, news_items: List[News], **kwargs) -> str:
        """格式化新闻摘要"""
        if not news_items:
            return "今日暂无新闻更新。"

        # 按分类统计
        category_count = {}
        for news in news_items:
            category_count[news.category] = category_count.get(news.category, 0) + 1

        # 构建摘要
        summary = f"📊 今日新闻摘要 (共{len(news_items)}条)\n\n"

        for category, count in category_count.items():
            summary += f"📰 {category}类: {count}条\n"

        summary += "\n🔥 热门新闻预览:\n"

        # 显示前3条新闻
        for i, news in enumerate(news_items[:3], 1):
            title = truncate_text(clean_text(news.title), 40)
            summary += f"{i}. {title}\n"

        return summary

class FormatterFactory:
    """格式化器工厂"""

    @staticmethod
    def create_formatter(formatter_type: str) -> MessageFormatter:
        """创建格式化器"""
        formatters = {
            'wechat': WechatTextFormatter,
            'markdown': MarkdownFormatter,
            'summary': SummaryFormatter
        }

        formatter_class = formatters.get(formatter_type.lower())
        if not formatter_class:
            raise ValueError(f"不支持的格式化器类型: {formatter_type}")

        return formatter_class()

    @staticmethod
    def get_supported_types() -> List[str]:
        """获取支持的格式化器类型"""
        return ['wechat', 'markdown', 'summary']

class NewsGroupFormatter:
    """新闻分组格式化器"""

    def __init__(self):
        self.wechat_formatter = WechatTextFormatter()

    def format_by_category(self, news_items: List[News]) -> str:
        """按分类格式化新闻"""
        if not news_items:
            return self.wechat_formatter._format_empty_message()

        # 按分类分组
        categories = {}
        for news in news_items:
            category = news.category
            if category not in categories:
                categories[category] = []
            categories[category].append(news)

        # 构建消息
        content = "📊 今日分类新闻 📊\n\n"

        for category, items in categories.items():
            content += f"📰 【{category}类】({len(items)}条)\n"

            # 显示该分类的前3条新闻
            for i, news in enumerate(items[:3], 1):
                title = truncate_text(clean_text(news.title), 35)
                content += f"  {i}. {title}\n"

            if len(items) > 3:
                content += f"  ... 还有{len(items)-3}条\n"

            content += "\n"

        return content.strip()

    def format_hot_news(self, news_items: List[News], limit: int = 5) -> str:
        """格式化热门新闻"""
        if not news_items:
            return "🔥 今日暂无热门新闻"

        # 按查看次数排序
        sorted_news = sorted(news_items, key=lambda x: x.view_count, reverse=True)[:limit]

        content = f"🔥 今日热门新闻 TOP{len(sorted_news)} 🔥\n\n"

        for i, news in enumerate(sorted_news, 1):
            title = truncate_text(clean_text(news.title), 40)
            content += f"{i}. {title}\n"
            content += f"   👁 {news.view_count}次 • 📰 {news.source_name}\n\n"

        return content.strip()