import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler import util
from django.conf import settings
from .models import VerificationCode

logger = logging.getLogger(__name__)


def cleanup_expired_codes():
    """Задача для очистки просроченных кодов верификации"""
    try:
        count = VerificationCode.cleanup_expired_codes()
        if count > 0:
            logger.info(f"Очищено {count} просроченных кодов верификации")
        else:
            logger.debug("Нет просроченных кодов для очистки")
    except Exception as e:
        logger.error(f"Ошибка при очистке просроченных кодов: {e}")

def start_scheduler():
    """Запуск APScheduler"""
    try:
        executors = {
            'default': ThreadPoolExecutor(max_workers=settings.SCHEDULER_SETTINGS['max_workers']),
        }
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 1,
            'misfire_grace_time': 30
        }
        
        scheduler = BackgroundScheduler(
            executors=executors,
            job_defaults=job_defaults,
            timezone=settings.TIME_ZONE
        )
        
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        scheduler.add_job(
            cleanup_expired_codes,
            'interval',
            minutes=settings.SCHEDULER_SETTINGS['cleanup_interval_minutes'],
            id='cleanup_expired_verification_codes',
            replace_existing=True,
            coalesce=True,
        )
        
        scheduler.start()
        logger.info("APScheduler успешно запущен")
        
        return scheduler
        
    except Exception as e:
        logger.error(f"Ошибка при запуске APScheduler: {e}")
        return None

def shutdown_scheduler(scheduler):
    """Остановка scheduler"""
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler остановлен")