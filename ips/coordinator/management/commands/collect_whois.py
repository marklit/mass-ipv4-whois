import json
from random import randint
from time import sleep

from django.conf import settings
from django.core.management.base import BaseCommand
from pykafka import KafkaClient
import redis

from ips.config import get_config


def save_to_redis(cidrs):
    try:
        redis_con = redis.StrictRedis(host=settings.REDIS_HOST,
                                      port=settings.REDIS_PORT,
                                      db=settings.REDIS_DB)
        redis_con.set('cidrs', ','.join(list(cidrs)))
    except Exception as exc:
        print exc


class Command(BaseCommand):
    help = 'Collect WHOIS results from Kafka'

    def handle(self, *args, **options):
        kafka_host = None

        while not kafka_host:
            kafka_host = get_config('KAFKA_HOST')

            if not kafka_host:
                print 'Unable to get Kafka host address, will try again.'
                sleep(randint(2, 5))

        client = KafkaClient(hosts=kafka_host)
        topic = client.topics['results']

        consumer = topic.get_simple_consumer()
        cidrs = set()

        for message in consumer:
            if message is None:
                continue

            if message.value and '{' in message.value:
                try:
                    msg = json.loads(message.value)
                except Exception as exc:
                    print exc
                    continue


                whois_key = 'whois' if 'whois' in msg else 'Whois'

                if  msg is None or \
                    whois_key not in msg or \
                    'asn_cidr' not in msg[whois_key] or \
                    msg[whois_key]['asn_cidr'] is None or \
                    msg[whois_key]['asn_cidr'] == 'NA':
                    continue

                old_len = len(cidrs)
                cidrs.add(str(msg[whois_key]['asn_cidr']))

                # Avoid saving the redis key again if it's not needed.
                if old_len != len(cidrs):
                    save_to_redis(cidrs)
