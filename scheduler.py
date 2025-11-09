"""
定时任务调度器模块
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import atexit
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rss_collector import rss_collector
from models import db_manager
from config import Config
from logger_config import app_logger


class NewsScheduler:
    """新闻收集定时任务调度器"""

    def __init__(self):
        # 配置任务存储和执行器
        jobstores = {
            'default': SQLAlchemyJobStore(url=Config.SQLALCHEMY_DATABASE_URI)
        }
        executors = {
            'default': ThreadPoolExecutor(20),
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }

        # 创建调度器
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults
        )

        # 初始化数据库
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        try:
            db_manager.init_db()
            app_logger.info("调度器数据库初始化成功")
        except Exception as e:
            app_logger.error(f"调度器数据库初始化失败: {e}")
            raise

    def start(self):
        """启动调度器"""
        try:
            # 添加RSS收集任务
            self.add_rss_collection_job()

            # 添加清理旧数据任务
            self.add_cleanup_job()

            # 启动调度器
            self.scheduler.start()
            app_logger.info("定时任务调度器启动成功")

            # 注册退出处理
            atexit.register(self.shutdown)

        except Exception as e:
            app_logger.error(f"调度器启动失败: {e}")
            raise

    def stop(self):
        """停止调度器"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                app_logger.info("定时任务调度器已停止")
        except Exception as e:
            app_logger.error(f"停止调度器失败: {e}")

    def shutdown(self):
        """关闭调度器（退出时调用）"""
        self.stop()
        # 关闭数据库连接
        db_manager.close_session()

    def add_rss_collection_job(self):
        """添加RSS收集定时任务"""
        try:
            # 解析定时时间
            hour, minute = map(int, Config.RSS_COLLECT_TIME.split(':'))

            # 创建Cron触发器
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                timezone='Asia/Shanghai'
            )

            # 添加任务
            job = self.scheduler.add_job(
                func=self._collect_news_job,
                trigger=trigger,
                id='rss_collection',
                name='RSS新闻收集任务',
                replace_existing=True,
                misfire_grace_time=300  # 允许5分钟的延迟执行
            )

            app_logger.info(f"RSS收集任务已添加，执行时间: 每天 {Config.RSS_COLLECT_TIME}")
            return job

        except Exception as e:
            app_logger.error(f"添加RSS收集任务失败: {e}")
            raise

    def add_cleanup_job(self):
        """添加数据清理定时任务"""
        try:
            # 每天凌晨2点执行清理任务
            trigger = CronTrigger(
                hour=2,
                minute=0,
                timezone='Asia/Shanghai'
            )

            # 添加任务
            job = self.scheduler.add_job(
                func=self._cleanup_job,
                trigger=trigger,
                id='data_cleanup',
                name='数据清理任务',
                replace_existing=True,
                misfire_grace_time=600  # 允许10分钟的延迟执行
            )

            app_logger.info("数据清理任务已添加，执行时间: 每天 02:00")
            return job

        except Exception as e:
            app_logger.error(f"添加数据清理任务失败: {e}")
            raise

    def _collect_news_job(self):
        """RSS收集任务执行函数"""
        try:
            app_logger.info("=" * 50)
            app_logger.info("开始执行定时RSS新闻收集任务")
            app_logger.info("=" * 50)

            # 执行新闻收集
            collected_count = rss_collector.collect_all_news()

            app_logger.info(f"定时RSS收集任务完成，共收集 {collected_count} 条新闻")

        except Exception as e:
            app_logger.error(f"RSS收集任务执行失败: {e}")
            # 不抛出异常，避免任务调度器停止

    def _cleanup_job(self):
        """数据清理任务执行函数"""
        try:
            app_logger.info("开始执行数据清理任务")

            # 清理旧新闻数据
            deleted_count = db_manager.clean_old_news(Config.DATA_RETENTION_DAYS)

            app_logger.info(f"数据清理任务完成，删除了 {deleted_count} 条旧记录")

        except Exception as e:
            app_logger.error(f"数据清理任务执行失败: {e}")
            # 不抛出异常，避免任务调度器停止

    def add_custom_job(self, func, trigger, job_id, name, **kwargs):
        """添加自定义任务"""
        try:
            job = self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=name,
                replace_existing=True,
                **kwargs
            )
            app_logger.info(f"自定义任务已添加: {name}")
            return job
        except Exception as e:
            app_logger.error(f"添加自定义任务失败: {e}")
            raise

    def remove_job(self, job_id):
        """移除任务"""
        try:
            self.scheduler.remove_job(job_id)
            app_logger.info(f"任务已移除: {job_id}")
        except Exception as e:
            app_logger.error(f"移除任务失败: {e}")

    def pause_job(self, job_id):
        """暂停任务"""
        try:
            self.scheduler.pause_job(job_id)
            app_logger.info(f"任务已暂停: {job_id}")
        except Exception as e:
            app_logger.error(f"暂停任务失败: {e}")

    def resume_job(self, job_id):
        """恢复任务"""
        try:
            self.scheduler.resume_job(job_id)
            app_logger.info(f"任务已恢复: {job_id}")
        except Exception as e:
            app_logger.error(f"恢复任务失败: {e}")

    def get_jobs(self):
        """获取所有任务信息"""
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
            return jobs
        except Exception as e:
            app_logger.error(f"获取任务信息失败: {e}")
            return []

    def trigger_rss_collection_now(self):
        """立即触发RSS收集任务"""
        try:
            app_logger.info("手动触发RSS收集任务")
            self.scheduler.add_job(
                func=self._collect_news_job,
                trigger='date',
                id='manual_rss_collection',
                name='手动RSS收集任务'
            )
            app_logger.info("手动RSS收集任务已添加到队列")
        except Exception as e:
            app_logger.error(f"手动触发RSS收集任务失败: {e}")

    def trigger_cleanup_now(self):
        """立即触发数据清理任务"""
        try:
            app_logger.info("手动触发数据清理任务")
            self.scheduler.add_job(
                func=self._cleanup_job,
                trigger='date',
                id='manual_cleanup',
                name='手动数据清理任务'
            )
            app_logger.info("手动数据清理任务已添加到队列")
        except Exception as e:
            app_logger.error(f"手动触发数据清理任务失败: {e}")


# 全局调度器实例
news_scheduler = NewsScheduler()


if __name__ == "__main__":
    """独立运行调度器"""
    try:
        app_logger.info("启动新闻收集调度器...")

        # 初始化数据库
        db_manager.init_db()

        # 启动调度器
        news_scheduler.start()

        # 立即执行一次RSS收集（可选）
        # news_scheduler.trigger_rss_collection_now()

        app_logger.info("调度器已启动，按 Ctrl+C 停止")

        # 保持程序运行
        import time
        while True:
            time.sleep(60)

    except KeyboardInterrupt:
        app_logger.info("收到停止信号，正在关闭调度器...")
        news_scheduler.shutdown()
        app_logger.info("调度器已关闭")
    except Exception as e:
        app_logger.error(f"调度器运行异常: {e}")
        news_scheduler.shutdown()
        sys.exit(1)