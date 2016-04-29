from uuid import uuid4

from bulk_update.helper import bulk_update
from django.http import HttpResponse

from coordinator.models import IPv4Address


def get_ips(request):
    request_id = str(uuid4())

    # Assign 987 IPs for this worker so that these IPs aren't assigned to
    # other workers. https://github.com/aykut/django-bulk-update/issues/46
    # says that SQLite3 will support up to 47 record updates per batch.
    for _ in range(0, 21):
        ids = list(IPv4Address.objects.filter(
                        allocated_for_request=None
                   ).values_list('id', flat=True)[:47])
        ips = IPv4Address.objects.filter(pk__in=ids)

        for ip in ips:
            ip.allocated_for_request = request_id

        bulk_update(ips, update_fields=['allocated_for_request'])

    ips = ','.join([ip.address
                    for ip in IPv4Address.objects.filter(
                        allocated_for_request=request_id)])

    if not ips:
        return HttpResponse('END') # No more IPs to work with

    return HttpResponse(ips)
