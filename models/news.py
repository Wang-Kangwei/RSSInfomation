"""
新闻数据模型
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from models.base import BaseModel

class News(BaseModel):
    """新闻表"""
    __tablename__ = 'news'

    title = Column(String(500), nullable=False, comment='新闻标题')
    summary = Column(Text, comment='新闻摘要')
    content = Column(Text, comment='新闻内容')
    link = Column(String(1000), nullable=False, comment='新闻链接')
    author = Column(String(100), comment='作者')
    category = Column(String(50), nullable=False, comment='新闻分类')
    source_name = Column(String(100), nullable=False, comment='RSS源名称')
    source_url = Column(String(500), nullable=False, comment='RSS源URL')
    pub_date = Column(DateTime, nullable=False, comment='发布时间')
    collect_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='收集时间')
    guid = Column(String(500), comment='RSS唯一标识')
    hash_code = Column(String(64), unique=True, nullable=False, comment='内容哈希值，用于去重')
    view_count = Column(Integer, default=0, nullable=False, comment='查看次数')
    is_published = Column(Boolean, default=True, nullable=False, comment='是否已发布')

    # 添加索引
    __table_args__ = (
        Index('idx_category', 'category'),
        Index('idx_pub_date', 'pub_date'),
        Index('idx_collect_time', 'collect_time'),
        Index('idx_hash_code', 'hash_code'),
        Index('idx_source_name', 'source_name'),
        Index('idx_is_published', 'is_published'),
        Index('idx_category_pub_date', 'category', 'pub_date'),
        {'comment': '新闻数据表'}
    )

    def to_dict(self):
        """转换为字典，格式化日期时间"""
        data = super().to_dict()
        data['pub_date'] = self.pub_date.isoformat() if self.pub_date else None
        data['collect_time'] = self.collect_time.isoformat() if self.collect_time else None
        data['created_time'] = self.created_time.isoformat() if self.created_time else None
        data['updated_time'] = self.updated_time.isoformat() if self.updated_time else None
        return data

    def increment_view_count(self):
        """增加查看次数"""
        self.view_count += 1

    def is_today_news(self) -> bool:
        """检查是否为今日新闻"""
        today = datetime.utcnow().date()
        return self.collect_time.date() == today

    def is_recent_news(self, days: int = 7) -> bool:
        """检查是否为最近几天的新闻"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.collect_time >= cutoff_date

    @staticmethod
    def generate_hash_code(title: str, link: str, pub_date: datetime) -> str:
        """生成内容哈希值用于去重"""
        import hashlib

        # 组合关键字段
        content = f"{title}{link}{pub_date.isoformat()}"

        # 生成SHA256哈希
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def __repr__(self):
        return f"<News(title='{self.title[:50]}...', category='{self.category}', source='{self.source_name}')>"