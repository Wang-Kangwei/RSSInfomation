"""
辅助函数库
"""

import re
import hashlib
import html
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin

def clean_text(text: str, max_length: int = None) -> str:
    """清理文本内容"""
    if not text:
        return ""

    # HTML解码
    text = html.unescape(text)

    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)

    # 清理多余空白
    text = re.sub(r'\s+', ' ', text.strip())

    # 限制长度
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip() + '...'

    return text

def clean_html(html_content: str, max_length: int = 1000) -> str:
    """清理HTML内容"""
    if not html_content:
        return ""

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()

        # 获取文本内容
        text = soup.get_text()

        # 清理空白
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        # 限制长度
        if len(text) > max_length:
            text = text[:max_length].rstrip() + '...'

        return text

    except ImportError:
        # 如果没有BeautifulSoup，使用简单清理
        return clean_text(html_content, max_length)

def generate_content_hash(title: str, link: str, pub_date: Optional[datetime] = None) -> str:
    """生成内容哈希值"""
    content = f"{title}{link}"
    if pub_date:
        content += pub_date.isoformat()

    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def validate_url(url: str) -> bool:
    """验证URL格式"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def normalize_url(url: str, base_url: str = None) -> str:
    """标准化URL"""
    if not url:
        return ""

    # 移除URL片段
    url = url.split('#')[0]

    # 如果有基础URL，处理相对URL
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)

    return url

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    if not dt:
        return ""
    return dt.strftime(format_str)

def format_date(dt: datetime, format_str: str = "%Y-%m-%d") -> str:
    """格式化日期"""
    if not dt:
        return ""
    return dt.strftime(format_str)

def time_ago(dt: datetime) -> str:
    """计算时间差（多久之前）"""
    if not dt:
        return ""

    now = datetime.utcnow()
    diff = now - dt

    if diff.days > 0:
        if diff.days == 1:
            return "1天前"
        else:
            return f"{diff.days}天前"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        if hours == 1:
            return "1小时前"
        else:
            return f"{hours}小时前"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        if minutes == 1:
            return "1分钟前"
        else:
            return f"{minutes}分钟前"
    else:
        return "刚刚"

def truncate_text(text: str, length: int = 100, suffix: str = "...") -> str:
    """截断文本"""
    if not text or len(text) <= length:
        return text or ""

    return text[:length].rstrip() + suffix

def extract_keywords(text: str, max_keywords: int = 5) -> list:
    """提取关键词（简单实现）"""
    if not text:
        return []

    # 简单的关键词提取：移除停用词，统计词频
    stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                  '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                  '这', '那', '她', '他', '它', '们', '这个', '那个', '什么', '怎么', '为什么'}

    # 分词（简单按空格和标点分割）
    words = re.findall(r'[\w]+', text.lower())

    # 过滤停用词和短词
    filtered_words = [word for word in words if len(word) > 1 and word not in stop_words]

    # 统计词频
    word_count = {}
    for word in filtered_words:
        word_count[word] = word_count.get(word, 0) + 1

    # 按频率排序，返回前N个
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:max_keywords]]

def safe_filename(filename: str) -> str:
    """生成安全的文件名"""
    # 移除或替换不安全的字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', '_', filename.strip())

    # 限制长度
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]

    return filename

def dict_to_xml(data: Dict[str, Any], root_tag: str = 'root') -> str:
    """将字典转换为XML（简单实现）"""
    def _dict_to_xml_element(d, parent_name='item'):
        if isinstance(d, dict):
            elements = []
            for key, value in d.items():
                if isinstance(value, (dict, list)):
                    elements.append(_dict_to_xml_element(value, key))
                else:
                    elements.append(f"<{key}>{str(value)}</{key}>")
            return f"<{parent_name}>" + "".join(elements) + f"</{parent_name}>"
        elif isinstance(d, list):
            elements = []
            for item in d:
                elements.append(_dict_to_xml_element(item, 'item'))
            return f"<{parent_name}>" + "".join(elements) + f"</{parent_name}>"
        else:
            return f"<{parent_name}>{str(d)}</{parent_name}>"

    return '<?xml version="1.0" encoding="UTF-8"?>' + _dict_to_xml_element(data, root_tag)

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f}{size_names[i]}"

def is_valid_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def extract_domain(url: str) -> str:
    """提取域名"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return ""

def mask_sensitive_info(text: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """遮蔽敏感信息"""
    if not text or len(text) <= visible_chars:
        return mask_char * len(text) if text else ""

    return text[:visible_chars] + mask_char * (len(text) - visible_chars)

def retry_on_exception(max_retries: int = 3, delay: float = 1.0):
    """重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise

                    time.sleep(delay * (2 ** attempt))  # 指数退避

            return None
        return wrapper
    return decorator

class RateLimiter:
    """简单的速率限制器"""

    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    def is_allowed(self) -> bool:
        """检查是否允许请求"""
        now = datetime.utcnow()

        # 清理过期的请求记录
        self.requests = [req_time for req_time in self.requests
                        if (now - req_time).total_seconds() < self.time_window]

        # 检查是否超过限制
        if len(self.requests) >= self.max_requests:
            return False

        # 记录当前请求
        self.requests.append(now)
        return True

    def get_reset_time(self) -> Optional[datetime]:
        """获取重置时间"""
        if not self.requests:
            return None

        oldest_request = min(self.requests)
        return oldest_request + timedelta(seconds=self.time_window)