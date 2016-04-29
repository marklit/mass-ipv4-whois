from django.conf.urls import url

from coordinator.views import get_ips


urlpatterns = [
    url(r'^$', get_ips, name='get_ips'),
]
