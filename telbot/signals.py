from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import ProfileModel
from .models import telbotid

@receiver(post_save, sender=ProfileModel)
def sync_credit_with_telbot(sender, instance, **kwargs):
    try:
        telbot_entry, created = TelbotId.objects.get_or_create(profile=instance)
        telbot_entry.credit = instance.credit
        telbot_entry.save()
    except Exception as e:
        print(f"Error syncing credit: {e}")
