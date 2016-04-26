from django.conf.urls import include, url


urlpatterns = [
    url(r'^coordinator/', include('coordinator.urls', namespace='coordinator')),
]
