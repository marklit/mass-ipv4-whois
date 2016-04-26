from django.db import models


class IPv4Address(models.Model):
    address = models.GenericIPAddressField()

    # This will be assigned a UUID so that it is only sent to one worker.
    # This should avoid a race condition.
    allocated_for_request = models.CharField(max_length=36, null=True)
