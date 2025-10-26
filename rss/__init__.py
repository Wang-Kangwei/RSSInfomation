"""
RSS feed parsing and collection module
"""

from .parser import RSSParser, StandardRSSParser, AtomRSSParser, NewsItem, RSSParserFactory
from .collector import RSSCollector
from .scheduler import RSSScheduler, get_scheduler, start_scheduler, stop_scheduler
from .sources import RSSSourceManager

__all__ = [
    'RSSParser', 'StandardRSSParser', 'AtomRSSParser', 'NewsItem', 'RSSParserFactory',
    'RSSCollector',
    'RSSScheduler', 'get_scheduler', 'start_scheduler', 'stop_scheduler',
    'RSSSourceManager'
]