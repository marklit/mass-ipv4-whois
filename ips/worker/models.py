from django.db import models
from model_utils.models import TimeStampedModel


class IPv4Whois(TimeStampedModel):
    STATUS_AWAITING_REGISTRY_LOOKUP = 0
    STATUS_LOOKING_UP_REGISTRY      = 1
    STATUS_LOOKUP_REGISTRY_FAILED   = 2
    STATUS_LOOKUP_REGISTRY_SUCCESS  = 3

    STATUS_LOOKING_UP_WHOIS         = 4
    STATUS_LOOKUP_WHOIS_FAILED      = 5
    STATUS_LOOKUP_WHOIS_SUCCESS     = 6
    STATUS_WITHIN_KNOWN_CIDR        = 7

    STATUSES = (
        (STATUS_AWAITING_REGISTRY_LOOKUP, 'Awaiting Registry'),
        (STATUS_LOOKING_UP_REGISTRY,      'Looking up Registry'),
        (STATUS_LOOKUP_REGISTRY_FAILED,   'Failed to find Registry'),
        (STATUS_LOOKUP_REGISTRY_SUCCESS,  'Found Registry'),
        (STATUS_LOOKING_UP_WHOIS,         'Looking up WHOIS'),
        (STATUS_LOOKUP_WHOIS_FAILED,      'Failed to lookup WHOIS'),
        (STATUS_LOOKUP_WHOIS_SUCCESS,     'Got WHOIS'),
        (STATUS_WITHIN_KNOWN_CIDR,        'Within Known CIDR Block'),
    )

    status  = models.PositiveSmallIntegerField(
                default=STATUS_AWAITING_REGISTRY_LOOKUP,
                choices=STATUSES)

    address = models.GenericIPAddressField()
    whois   = models.TextField(null=True)
