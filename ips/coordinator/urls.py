from django.conf.urls import url

from coordinator.views import get_ips, cidr_hit


urlpatterns = [
    url(r'^cidr\-hit/(?P<ip_address>[0-9\.]*)/$', cidr_hit, name='cidr_hit'),
    url(r'^$', get_ips, name='get_ips'),
]
