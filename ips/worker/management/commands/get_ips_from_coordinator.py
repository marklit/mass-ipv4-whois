from random import randint
from time import sleep
from urlparse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand
import netaddr
import redis
import requests

from ips.config import get_config
from worker.models import IPv4Whois
from worker.tasks import (whois_afrinic,
                          whois_apnic,
                          whois_arin,
                          whois_lacnic,
                          whois_ripencc)


def in_known_cidr_block(ip_address):
    redis_con = redis.StrictRedis(host=settings.REDIS_HOST,
                                  port=settings.REDIS_PORT,
                                  db=settings.REDIS_DB)
    cidrs = redis_con.get('cidrs')

    if not cidrs or not len(cidrs):
        return False

    return len(netaddr.all_matching_cidrs(ip_address, cidrs.split(','))) > 0


class Command(BaseCommand):
    help = 'Get IPs to lookup from coordinator'

    def handle(self, *args, **options):
        lookup = {
            'rdap.afrinic.net': whois_afrinic,
            'rdap.apnic.net':   whois_apnic,
            'rdap.arin.net':    whois_arin,
            'rdap.lacnic.net':  whois_lacnic,
            'rdap.db.ripe.net': whois_ripencc,
        }
        bootstrap_url = 'http://rdap.arin.net/bootstrap/ip/%s'

        while True:
            # get 10,000 IPs from coordinator
            coordinator_endpoint = get_config('COORDINATOR_ENDPOINT')

            if not coordinator_endpoint:
                print 'Unable to get coordinator address, will try later'
                sleep(randint(3, 15))
                continue

            # Make sure there is a Kafka endpoint to report results back to
            # before continuing
            kafka_host = get_config('KAFKA_HOST')

            if not kafka_host:
                print 'No Kafka host to report back to, will try later'
                sleep(randint(3, 15))
                continue

            try:
                resp = requests.get(coordinator_endpoint, timeout=120)
            except Exception as exc:
                print exc
                print 'Sleeping for a bit to give the coordinator a break'
                sleep(randint(3, 8))
                continue

            if resp.status_code != 200:
                # Coordinator might no be up, try later.
                print 'Got non-HTTP 200 back from coordinator, will try later'
                sleep(5)
                continue

            if resp.text.strip().upper() == 'END':
                # No more IPs to work with or the list hasn't finished
                # generating yet
                print 'No more IPs from coordinator, will check back later'
                sleep(30)
                continue

            # Find the Registry for each IP
            for ip in resp.text.split(','):
                # validate ip here

                _ip = IPv4Whois(address=ip)
                _ip.save()

                if in_known_cidr_block(ip):
                    _ip.status = IPv4Whois.STATUS_WITHIN_KNOWN_CIDR
                    _ip.save()
                    continue

                try:
                    resp = requests.head(bootstrap_url % ip, timeout=10)
                except Exception as exc:
                    print exc
                    _ip.status = IPv4Whois.STATUS_LOOKUP_REGISTRY_FAILED
                    _ip.save()
                    continue

                if 'Location' not in resp.headers:
                    _ip.status = IPv4Whois.STATUS_LOOKUP_REGISTRY_FAILED
                    _ip.save()
                    continue

                url = urlparse(resp.headers['Location'])
                rdap_host = url.netloc.lower().strip()

                if rdap_host in lookup:
                    _ip.status = IPv4Whois.STATUS_LOOKUP_REGISTRY_SUCCESS
                    _ip.save()
                    # Queue Registry-specific WHOIS lookup
                    lookup[rdap_host].delay(_ip.pk)
                else:
                    _ip.status = IPv4Whois.STATUS_LOOKUP_REGISTRY_FAILED
                    _ip.save()
