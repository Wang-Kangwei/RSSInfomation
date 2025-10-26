"""
自定义异常类
"""

class RSSInfomationError(Exception):
    """RSSInfomation基础异常类"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ConfigurationError(RSSInfomationError):
    """配置错误"""
    pass

class DatabaseError(RSSInfomationError):
    """数据库错误"""
    pass

class RSSParseError(RSSInfomationError):
    """RSS解析错误"""
    pass

class RSSFetchError(RSSInfomationError):
    """RSS获取错误"""
    pass

class WeChatAPIError(RSSInfomationError):
    """微信API错误"""
    pass

class NewsNotFoundError(RSSInfomationError):
    """新闻未找到错误"""
    pass

class ValidationError(RSSInfomationError):
    """数据验证错误"""
    pass

class ServiceUnavailableError(RSSInfomationError):
    """服务不可用错误"""
    pass