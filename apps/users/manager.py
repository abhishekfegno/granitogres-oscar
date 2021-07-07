from django.db import models


class ActiveOTPManager(models.Manager):

    def get_queryset(self):
        return super(ActiveOTPManager, self).get_queryset().filter(is_active=True)
