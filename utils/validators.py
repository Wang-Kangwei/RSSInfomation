"""
数据验证工具
"""

import re
from typing import Any, List, Dict, Optional
from datetime import datetime
from urllib.parse import urlparse

from core.exceptions import ValidationError
from utils.helpers import validate_url

class Validator:
    """基础验证器"""

    @staticmethod
    def required(value: Any, field_name: str = "字段") -> Any:
        """验证必填字段"""
        if value is None or value == "":
            raise ValidationError(f"{field_name}不能为空")
        return value

    @staticmethod
    def max_length(value: str, max_len: int, field_name: str = "字段") -> str:
        """验证最大长度"""
        if value and len(value) > max_len:
            raise ValidationError(f"{field_name}长度不能超过{max_len}个字符")
        return value

    @staticmethod
    def min_length(value: str, min_len: int, field_name: str = "字段") -> str:
        """验证最小长度"""
        if value and len(value) < min_len:
            raise ValidationError(f"{field_name}长度不能少于{min_len}个字符")
        return value

    @staticmethod
    def email(value: str, field_name: str = "邮箱") -> str:
        """验证邮箱格式"""
        if value:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, value):
                raise ValidationError(f"{field_name}格式不正确")
        return value

    @staticmethod
    def url(value: str, field_name: str = "URL") -> str:
        """验证URL格式"""
        if value and not validate_url(value):
            raise ValidationError(f"{field_name}格式不正确")
        return value

    @staticmethod
    def numeric(value: Any, field_name: str = "数值") -> Any:
        """验证数字"""
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                raise ValidationError(f"{field_name}必须是数字")
        return value

    @staticmethod
    def integer(value: Any, field_name: str = "整数") -> int:
        """验证整数"""
        if value is not None:
            try:
                return int(value)
            except (ValueError, TypeError):
                raise ValidationError(f"{field_name}必须是整数")
        return value

    @staticmethod
    def positive(value: Any, field_name: str = "数值") -> Any:
        """验证正数"""
        value = Validator.numeric(value, field_name)
        if value is not None and value <= 0:
            raise ValidationError(f"{field_name}必须是正数")
        return value

    @staticmethod
    def range(value: Any, min_val: float, max_val: float, field_name: str = "数值") -> float:
        """验证数值范围"""
        value = Validator.numeric(value, field_name)
        if value is not None and (value < min_val or value > max_val):
            raise ValidationError(f"{field_name}必须在{min_val}到{max_val}之间")
        return value

    @staticmethod
    def choices(value: Any, choices: List[Any], field_name: str = "选项") -> Any:
        """验证选项"""
        if value is not None and value not in choices:
            raise ValidationError(f"{field_name}必须是以下选项之一: {', '.join(map(str, choices))}")
        return value

    @staticmethod
    def regex(value: str, pattern: str, field_name: str = "字段") -> str:
        """验证正则表达式"""
        if value and not re.match(pattern, value):
            raise ValidationError(f"{field_name}格式不正确")
        return value

class NewsValidator:
    """新闻验证器"""

    @staticmethod
    def validate_title(title: str) -> str:
        """验证新闻标题"""
        title = Validator.required(title, "标题")
        title = Validator.max_length(title, 500, "标题")
        title = Validator.min_length(title, 3, "标题")
        return title.strip()

    @staticmethod
    def validate_summary(summary: str) -> str:
        """验证新闻摘要"""
        summary = Validator.max_length(summary, 2000, "摘要")
        return summary.strip() if summary else ""

    @staticmethod
    def validate_content(content: str) -> str:
        """验证新闻内容"""
        content = Validator.max_length(content, 10000, "内容")
        return content.strip() if content else ""

    @staticmethod
    def validate_link(link: str) -> str:
        """验证新闻链接"""
        link = Validator.required(link, "链接")
        link = Validator.url(link, "链接")
        link = Validator.max_length(link, 1000, "链接")
        return link.strip()

    @staticmethod
    def validate_author(author: str) -> str:
        """验证作者"""
        author = Validator.max_length(author, 100, "作者")
        return author.strip() if author else ""

    @staticmethod
    def validate_category(category: str) -> str:
        """验证分类"""
        category = Validator.required(category, "分类")
        category = Validator.max_length(category, 50, "分类")
        return category.strip()

    @staticmethod
    def validate_source_name(source_name: str) -> str:
        """验证RSS源名称"""
        source_name = Validator.required(source_name, "RSS源名称")
        source_name = Validator.max_length(source_name, 100, "RSS源名称")
        return source_name.strip()

    @staticmethod
    def validate_source_url(source_url: str) -> str:
        """验证RSS源URL"""
        source_url = Validator.required(source_url, "RSS源URL")
        source_url = Validator.url(source_url, "RSS源URL")
        source_url = Validator.max_length(source_url, 500, "RSS源URL")
        return source_url.strip()

    @staticmethod
    def validate_guid(guid: str) -> str:
        """验证GUID"""
        guid = Validator.max_length(guid, 500, "GUID")
        return guid.strip() if guid else ""

    @staticmethod
    def validate_hash_code(hash_code: str) -> str:
        """验证哈希值"""
        hash_code = Validator.required(hash_code, "哈希值")
        hash_code = Validator.regex(hash_code, r'^[a-fA-F0-9]{64}$', "哈希值")
        return hash_code.strip()

    @staticmethod
    def validate_news_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """验证新闻数据"""
        validated_data = {}

        validated_data['title'] = NewsValidator.validate_title(data.get('title', ''))
        validated_data['summary'] = NewsValidator.validate_summary(data.get('summary', ''))
        validated_data['content'] = NewsValidator.validate_content(data.get('content', ''))
        validated_data['link'] = NewsValidator.validate_link(data.get('link', ''))
        validated_data['author'] = NewsValidator.validate_author(data.get('author', ''))
        validated_data['category'] = NewsValidator.validate_category(data.get('category', ''))
        validated_data['source_name'] = NewsValidator.validate_source_name(data.get('source_name', ''))
        validated_data['source_url'] = NewsValidator.validate_source_url(data.get('source_url', ''))
        validated_data['guid'] = NewsValidator.validate_guid(data.get('guid', ''))
        validated_data['hash_code'] = NewsValidator.validate_hash_code(data.get('hash_code', ''))

        return validated_data

class RSSSourceValidator:
    """RSS源验证器"""

    @staticmethod
    def validate_name(name: str) -> str:
        """验证RSS源名称"""
        name = Validator.required(name, "RSS源名称")
        name = Validator.max_length(name, 100, "RSS源名称")
        name = Validator.min_length(name, 2, "RSS源名称")
        return name.strip()

    @staticmethod
    def validate_url(url: str) -> str:
        """验证RSS源URL"""
        url = Validator.required(url, "RSS源URL")
        url = Validator.url(url, "RSS源URL")
        url = Validator.max_length(url, 500, "RSS源URL")

        # 额外验证：检查是否为RSS常见的URL模式
        if not any(pattern in url.lower() for pattern in ['/rss', '/feed', '.xml', 'rss.xml', 'feed.xml']):
            # 不是强制要求，但给出警告
            pass

        return url.strip()

    @staticmethod
    def validate_category(category: str) -> str:
        """验证分类"""
        category = Validator.required(category, "分类")
        category = Validator.max_length(category, 50, "分类")
        return category.strip()

    @staticmethod
    def validate_description(description: str) -> str:
        """验证描述"""
        description = Validator.max_length(description, 500, "描述")
        return description.strip() if description else ""

    @staticmethod
    def validate_fetch_interval(interval: Any) -> int:
        """验证抓取间隔"""
        interval = Validator.integer(interval, "抓取间隔")
        interval = Validator.positive(interval, "抓取间隔")
        interval = Validator.range(interval, 60, 86400, "抓取间隔")  # 1分钟到24小时
        return interval

    @staticmethod
    def validate_rss_source_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """验证RSS源数据"""
        validated_data = {}

        validated_data['name'] = RSSSourceValidator.validate_name(data.get('name', ''))
        validated_data['url'] = RSSSourceValidator.validate_url(data.get('url', ''))
        validated_data['category'] = RSSSourceValidator.validate_category(data.get('category', ''))
        validated_data['description'] = RSSSourceValidator.validate_description(data.get('description', ''))
        validated_data['fetch_interval'] = RSSSourceValidator.validate_fetch_interval(
            data.get('fetch_interval', 3600)
        )

        # 布尔值验证
        is_active = data.get('is_active', True)
        if isinstance(is_active, str):
            is_active = is_active.lower() in ('true', '1', 'yes', 'on')
        validated_data['is_active'] = bool(is_active)

        return validated_data

class SystemConfigValidator:
    """系统配置验证器"""

    @staticmethod
    def validate_config_key(key: str) -> str:
        """验证配置键"""
        key = Validator.required(key, "配置键")
        key = Validator.max_length(key, 100, "配置键")
        key = Validator.regex(key, r'^[a-zA-Z][a-zA-Z0-9_]*$', "配置键")
        return key.strip()

    @staticmethod
    def validate_config_value(value: str) -> str:
        """验证配置值"""
        if value is not None:
            value = str(value)
        return value or ""

    @staticmethod
    def validate_description(description: str) -> str:
        """验证描述"""
        description = Validator.max_length(description, 500, "描述")
        return description.strip() if description else ""

    @staticmethod
    def validate_system_config_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """验证系统配置数据"""
        validated_data = {}

        validated_data['config_key'] = SystemConfigValidator.validate_config_key(data.get('config_key', ''))
        validated_data['config_value'] = SystemConfigValidator.validate_config_value(data.get('config_value'))
        validated_data['description'] = SystemConfigValidator.validate_description(data.get('description', ''))

        return validated_data

class PaginationValidator:
    """分页验证器"""

    @staticmethod
    def validate_page(page: Any) -> int:
        """验证页码"""
        page = Validator.integer(page, "页码")
        page = Validator.positive(page, "页码")
        return max(1, page)  # 至少为1

    @staticmethod
    def validate_per_page(per_page: Any, max_per_page: int = 100) -> int:
        """验证每页数量"""
        per_page = Validator.integer(per_page, "每页数量")
        per_page = Validator.positive(per_page, "每页数量")
        per_page = Validator.range(per_page, 1, max_per_page, "每页数量")
        return per_page

    @staticmethod
    def validate_pagination_params(data: Dict[str, Any], max_per_page: int = 100) -> Dict[str, int]:
        """验证分页参数"""
        page = PaginationValidator.validate_page(data.get('page', 1))
        per_page = PaginationValidator.validate_per_page(data.get('per_page', 20), max_per_page)

        return {
            'page': page,
            'per_page': per_page,
            'offset': (page - 1) * per_page
        }