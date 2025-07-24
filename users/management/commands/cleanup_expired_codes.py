import time
import logging
from django.core.management.base import BaseCommand
from users.scheduler import start_scheduler

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run APScheduler for background tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=600,
            help='Interval in seconds between manual cleanup runs (default: 600)',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        
        self.stdout.write(
            self.style.SUCCESS(f'Запуск APScheduler с интервалом {interval} секунд')
        )
        
        scheduler = start_scheduler()
        
        if scheduler:
            self.stdout.write(
                self.style.SUCCESS('APScheduler успешно запущен')
            )
            
            try:
                while True:
                    time.sleep(interval)
                    self.stdout.write(
                        self.style.NOTICE('Проверка просроченных кодов...')
                    )
            except KeyboardInterrupt:
                scheduler.shutdown()
                self.stdout.write(
                    self.style.WARNING('APScheduler остановлен пользователем')
                )
        else:
            self.stdout.write(
                self.style.ERROR('Не удалось запустить APScheduler')
            )