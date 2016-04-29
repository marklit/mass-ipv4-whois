from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import redis


class Command(BaseCommand):
    help = 'Set cluster configuration'

    def add_arguments(self, parser):
        parser.add_argument('coordinator-private-ip', type=str)

    def handle(self, *args, **options):
        if not options['coordinator-private-ip']:
            raise CommandError('Coordinator IP needs to be an IP address')

        coord_ip = options['coordinator-private-ip'].strip()

        redis_con = redis.StrictRedis(host=settings.REDIS_HOST,
                                      port=settings.REDIS_PORT,
                                      db=settings.REDIS_DB)
        redis_con.set('KAFKA_HOST',
                      '%s:9092' % coord_ip)
        redis_con.set('COORDINATOR_ENDPOINT',
                      'http://%s:8000/coordinator/' % coord_ip)
