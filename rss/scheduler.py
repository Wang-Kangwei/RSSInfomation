"""
RSS定时任务调度器
"""

import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from core.database import get_db_session
from models.news import News
from models.source import RSSSource
from rss.collector import RSSCollector
from utils.logger import get_logger

logger = get_logger(__name__)

class RSSScheduler:
    """RSS定时任务调度器"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.scheduler = BackgroundScheduler()
        max_news_per_source = self.config.get('max_news_per_source', 10)
        self.collector = RSSCollector(max_news_per_source=max_news_per_source)
        self.is_running = False
        self.job_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'last_execution': None,
            'last_success': None,
            'last_error': None
        }

    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行中")
            return

        try:
            # 添加事件监听器
            self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)

            # 添加定时任务
            self._setup_jobs()

            # 启动调度器
            self.scheduler.start()
            self.is_running = True

            logger.info("RSS调度器启动成功")

        except Exception as e:
            logger.error(f"RSS调度器启动失败: {e}")
            raise

    def stop(self):
        """停止调度器"""
        if not self.is_running:
            logger.warning("调度器未在运行")
            return

        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("RSS调度器已停止")

        except Exception as e:
            logger.error(f"RSS调度器停止失败: {e}")

    def _setup_jobs(self):
        """设置定时任务"""
        # 每日定时收集任务
        collect_hour = self.config.get('collect_hour', 5)
        self.scheduler.add_job(
            func=self._daily_collection_job,
            trigger=CronTrigger(hour=collect_hour, minute=0),
            id='daily_collection',
            name='每日RSS收集任务',
            replace_existing=True
        )

        # 每小时检查RSS源健康状态
        self.scheduler.add_job(
            func=self._health_check_job,
            trigger=CronTrigger(minute=30),  # 每小时30分执行
            id='health_check',
            name='RSS源健康检查',
            replace_existing=True
        )

        # 每6小时清理过期数据
        self.scheduler.add_job(
            func=self._cleanup_job,
            trigger=CronTrigger(hour='*/6'),  # 每6小时执行
            id='data_cleanup',
            name='过期数据清理',
            replace_existing=True
        )

        # 每15分钟执行增量收集（用于实时性要求高的RSS源）
        self.scheduler.add_job(
            func=self._incremental_collection_job,
            trigger=IntervalTrigger(minutes=15),
            id='incremental_collection',
            name='增量RSS收集',
            replace_existing=True
        )

        logger.info("定时任务设置完成")

    def _daily_collection_job(self):
        """每日收集任务"""
        logger.info("开始执行每日RSS收集任务")
        start_time = datetime.utcnow()

        try:
            # 获取所有活跃的RSS源
            session = get_db_session()
            sources = session.query(RSSSource).filter(RSSSource.is_active == True).all()

            total_news = 0
            success_count = 0
            error_count = 0

            for source in sources:
                try:
                    news_count = self.collector.collect_from_source(source.id)
                    total_news += news_count
                    success_count += 1
                    logger.info(f"从 {source.name} 收集到 {news_count} 条新闻")

                except Exception as e:
                    error_count += 1
                    logger.error(f"从 {source.name} 收集新闻失败: {e}")

            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"每日RSS收集任务完成: 成功{success_count}个源, 失败{error_count}个源, "
                       f"共收集{total_news}条新闻, 耗时{duration:.2f}秒")

        except Exception as e:
            logger.error(f"每日RSS收集任务执行失败: {e}")
            raise

    def _incremental_collection_job(self):
        """增量收集任务"""
        logger.debug("开始执行增量RSS收集任务")

        try:
            # 获取需要增量收集的RSS源（设置较短抓取间隔的源）
            session = get_db_session()
            sources = session.query(RSSSource).filter(
                RSSSource.is_active == True,
                RSSSource.fetch_interval <= 900  # 15分钟
            ).all()

            if not sources:
                return

            total_news = 0
            for source in sources:
                try:
                    news_count = self.collector.collect_from_source(source.id)
                    total_news += news_count
                    if news_count > 0:
                        logger.info(f"增量收集: 从 {source.name} 收集到 {news_count} 条新闻")

                except Exception as e:
                    logger.warning(f"增量收集失败 {source.name}: {e}")

            if total_news > 0:
                logger.info(f"增量收集完成: 共收集{total_news}条新闻")

        except Exception as e:
            logger.error(f"增量收集任务执行失败: {e}")

    def _health_check_job(self):
        """健康检查任务"""
        logger.debug("开始执行RSS源健康检查")

        try:
            session = get_db_session()

            # 检查长时间未成功抓取的源
            unhealthy_threshold = datetime.utcnow() - timedelta(hours=24)
            unhealthy_sources = session.query(RSSSource).filter(
                RSSSource.is_active == True,
                RSSSource.last_success_time < unhealthy_threshold
            ).all()

            for source in unhealthy_sources:
                logger.warning(f"RSS源不健康: {source.name}, 最后成功时间: {source.last_success_time}")

            # 检查连续错误次数过多的源
            error_sources = session.query(RSSSource).filter(
                RSSSource.is_active == True,
                RSSSource.error_count >= 5
            ).all()

            for source in error_sources:
                logger.warning(f"RSS源连续错误过多: {source.name}, 错误次数: {source.error_count}")

            # 生成健康报告
            total_sources = session.query(RSSSource).filter(RSSSource.is_active == True).count()
            healthy_count = total_sources - len(unhealthy_sources) - len(error_sources)

            logger.info(f"健康检查完成: 总计{total_sources}个源, 健康{healthy_count}个, "
                       f"不健康{len(unhealthy_sources)}个, 连续错误{len(error_sources)}个")

        except Exception as e:
            logger.error(f"健康检查任务执行失败: {e}")

    def _cleanup_job(self):
        """数据清理任务"""
        logger.info("开始执行过期数据清理")

        try:
            session = get_db_session()

            # 获取保留天数配置
            retention_days = self.config.get('retention_days', 7)
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            # 统计要删除的数据
            old_news_count = session.query(News).filter(
                News.collect_time < cutoff_date
            ).count()

            if old_news_count > 0:
                # 删除过期新闻
                deleted_count = session.query(News).filter(
                    News.collect_time < cutoff_date
                ).delete()

                session.commit()
                logger.info(f"数据清理完成: 删除了 {deleted_count} 条过期新闻")
            else:
                logger.info("没有需要清理的过期数据")

        except Exception as e:
            logger.error(f"数据清理任务执行失败: {e}")
            if 'session' in locals():
                session.rollback()

    def _job_executed(self, event):
        """任务执行成功事件处理"""
        self.job_stats['total_executions'] += 1
        self.job_stats['successful_executions'] += 1
        self.job_stats['last_execution'] = datetime.utcnow()
        self.job_stats['last_success'] = datetime.utcnow()

        logger.debug(f"任务执行成功: {event.job_id}")

    def _job_error(self, event):
        """任务执行失败事件处理"""
        self.job_stats['total_executions'] += 1
        self.job_stats['failed_executions'] += 1
        self.job_stats['last_execution'] = datetime.utcnow()
        self.job_stats['last_error'] = datetime.utcnow()

        logger.error(f"任务执行失败: {event.job_id}, 异常: {event.exception}")

    def get_job_status(self) -> Dict[str, Any]:
        """获取任务状态"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })

        return {
            'is_running': self.is_running,
            'jobs': jobs,
            'statistics': self.job_stats.copy()
        }

    def trigger_manual_collection(self, source_id: int = None):
        """手动触发收集任务"""
        logger.info(f"手动触发RSS收集: source_id={source_id}")

        try:
            if source_id:
                # 收集指定RSS源
                news_count = self.collector.collect_from_source(source_id)
                logger.info(f"手动收集完成: 收集到 {news_count} 条新闻")
            else:
                # 收集所有RSS源
                session = get_db_session()
                sources = session.query(RSSSource).filter(RSSSource.is_active == True).all()

                total_news = 0
                for source in sources:
                    try:
                        news_count = self.collector.collect_from_source(source.id)
                        total_news += news_count
                    except Exception as e:
                        logger.error(f"手动收集失败 {source.name}: {e}")

                logger.info(f"手动收集完成: 总共收集到 {total_news} 条新闻")

        except Exception as e:
            logger.error(f"手动收集失败: {e}")
            raise

# 全局调度器实例
_scheduler_instance = None

def get_scheduler(config: Dict[str, Any] = None) -> RSSScheduler:
    """获取调度器单例实例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = RSSScheduler(config)
    return _scheduler_instance

def start_scheduler(config: Dict[str, Any] = None):
    """启动调度器"""
    scheduler = get_scheduler(config)
    scheduler.start()
    return scheduler

def stop_scheduler():
    """停止调度器"""
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.stop()
        _scheduler_instance = None