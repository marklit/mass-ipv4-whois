from random import shuffle

from django.core.management.base import BaseCommand
import ipaddr

from coordinator.models import IPv4Address


CHUNK_SIZES = 10000


def chunks(l, n):
    """
    Yield successive n-sized chunks from l.

    From: http://stackoverflow.com/a/312464
    """
    for i in range(0, len(l), n):
        yield l[i:i+n]


def is_reserved(ip):
    return (ipaddr.IPv4Network(ip).is_multicast |
            ipaddr.IPv4Network(ip).is_private |
            ipaddr.IPv4Network(ip).is_link_local |
            ipaddr.IPv4Network(ip).is_loopback |
            ipaddr.IPv4Network(ip).is_reserved)


def get_ips():
    """
    This will return 4,706,768 addresses.
    """
    for class_a in range(1, 256):
        # Exclude some known single-owner and/or reserved class A's
        if class_a in (3, 9, 10, 12, 15, 16, 17, 18, 19, 20, 34, 48, 56, 127):
            continue

        for class_b in range(0, 256):
            for class_c in range(0, 256, 12):
                for class_d in range(1, 256, 64):
                    ip = '%d.%d.%d.%d' % (class_a, class_b, class_c, class_d)

                    if not is_reserved(ip):
                        yield ip


class Command(BaseCommand):
    help = 'Generate a list of ~4.5 IPv4 addresses'

    def handle(self, *args, **options):
        ips = [ip for ip in get_ips()]
        # Increase the changes different worker nodes start at widely different
        # areas of the IPv4 address space. When they're assigned their 3rd or
        # 4th batch of IPs onward they hopefully will have lots of CIDR hits
        # and no need to conduct as many lookups.
        shuffle(ips)

        # Make sure we don't generate the list twice
        IPv4Address.objects.all().delete()

        # Save <CHUNK_SIZES> IPs at a time to lower overhead
        for count, ips in enumerate(chunks(ips, CHUNK_SIZES), start=1):
            IPv4Address.objects.bulk_create([
                IPv4Address(address=ip)
                for ip in ips
            ])
            print '{:,}'.format(count * CHUNK_SIZES)
