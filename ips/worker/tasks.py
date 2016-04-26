from datetime import datetime
import json

from celery.decorators import periodic_task, task
from celery.task.schedules import crontab
from django.conf import settings
from django.db.models import Count
from ipwhois import IPWhois
from pykafka import KafkaClient

from worker.models import IPv4Whois


def send_to_kafka(topic_name, msg):
    client = KafkaClient(hosts=settings.KAFKA_HOST)
    topic = client.topics[topic_name]

    with topic.get_producer(delivery_reports=True) as producer:
        producer.produce(json.dumps(msg, sort_keys=True))

        msg, exc = producer.get_delivery_report(block=True)

        if exc is not None:
            raise exc


def _whois(ip_pk):
    ip = IPv4Whois.objects.get(pk=ip_pk)
    ip.status = IPv4Whois.STATUS_LOOKING_UP_WHOIS
    ip.save()

    obj = IPWhois(ip.address, timeout=9)

    try:
        results = obj.lookup_rdap()
    except Exception as exc:
        ip.status = IPv4Whois.STATUS_LOOKUP_WHOIS_FAILED
        ip.save()
        raise exc

    ip.whois = json.dumps(results)
    ip.status = IPv4Whois.STATUS_LOOKUP_WHOIS_SUCCESS
    ip.save()

    kafka_msg = {
        'IP': ip.address,
        'Whois': results,
        'Host': settings.EXTERNAL_IP,
        'Timestamp': datetime.utcnow().isoformat(),
    }
    send_to_kafka('results', kafka_msg)


@task(default_retry_delay=600,
      max_retries=3,
      timeout=10,
      rate_limit='10/s')
def whois_arin(ip_pk, *args, **kwargs):
    _whois(ip_pk)


@task(default_retry_delay=600,
      max_retries=3,
      timeout=10,
      rate_limit='10/s')
def whois_ripencc(ip_pk, *args, **kwargs):
    _whois(ip_pk)


@task(default_retry_delay=600,
      max_retries=3,
      timeout=10,
      rate_limit='10/s')
def whois_apnic(ip_pk, *args, **kwargs):
    _whois(ip_pk)


@task(default_retry_delay=600,
      max_retries=3,
      timeout=10,
      rate_limit='1/s')
def whois_lacnic(ip_pk, *args, **kwargs):
    _whois(ip_pk)


@task(default_retry_delay=600,
      max_retries=3,
      timeout=10,
      rate_limit='1/s')
def whois_afrinic(ip_pk, *args, **kwargs):
    _whois(ip_pk)


@periodic_task(run_every=crontab(minute="*/1"),
               timeout=45)
def report_metrics(*args, **kwargs):
    kafka_msg = {IPv4Whois.STATUSES[stat['status']][1]: stat['total']
                 for stat in IPv4Whois.objects
                                      .all()
                                      .values('status')
                                      .annotate(total=Count('status'))}

    kafka_msg['Host'] = settings.EXTERNAL_IP
    kafka_msg['Timestamp'] = datetime.utcnow().isoformat()
    send_to_kafka('metrics', kafka_msg)
