import json
from itertools import chain
from random import randint
from time import sleep

from django.core.management.base import BaseCommand
from pykafka import KafkaClient

from ips.config import get_config


class Command(BaseCommand):
    help = 'Monitor telemetry from workers'

    def handle(self, *args, **options):
        kafka_host = None

        while not kafka_host:
            kafka_host = get_config('KAFKA_HOST')

            if not kafka_host:
                print 'Unable to get Kafka host address, will try again.'
                sleep(randint(2, 5))

        client = KafkaClient(hosts=kafka_host)
        topic = client.topics['metrics']

        consumer = topic.get_simple_consumer()
        stats = {}

        for message in consumer:
            if message is None:
                continue

            if message.value and '{' in message.value:
                try:
                    line = json.loads(message.value)
                except Exception as exc:
                    print exc
                    continue
            else:
                continue

            if type(line) is not dict or \
               not 'Host' in line or \
               not line['Host'] or \
               not line['Host'].strip():
                continue

            if not line['Host'] in stats:
                stats[line['Host']] = {}

            for key in line.keys():
                # Skip known keys with non-integer values
                if key in ('Host', 'Timestamp'):
                    continue

                # Only sum up values that are integers
                try:
                    stats[line['Host']][key] = int(line[key])
                except (KeyError, ValueError) as exc:
                    pass

            # Aggregate telemetry
            keys = set(list(chain(*[stats[host].keys()
                                    for host in stats])))

            aggregates = {key: 0 for key in keys}

            for host in stats:
                for key in keys:
                    if key in stats[host]:
                        aggregates[key] = aggregates[key] + stats[host][key]

            # Print the keys sorted by name so hopefully you can eye-ball
            # changing values better.
            print json.dumps(aggregates, sort_keys=True)
