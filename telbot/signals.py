from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import ProfileModel
from .models import telbotid

@receiver(post_save, sender=telbotid)
def sync_profile_credit_from_telbot(sender, instance, **kwargs):
    if hasattr(instance, '_syncing'):
        return
    instance._syncing = True
    profile = instance.profile
    if profile and profile.credit != instance.credit:
        profile.credit = instance.credit
        profile._syncing = True
        profile.save()
    del instance._syncing