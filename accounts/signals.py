from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import ProfileModel
from products.models import Store


@receiver(post_save, sender=ProfileModel)
def set_default_store(sender, instance, created, **kwargs):

    if not created:
        return

    if instance.server_store_id:
        return

    store = Store.objects.filter(
        name="Intelleum"
    ).first()

    if store:
        instance.server_store = store
        instance.save(update_fields=["server_store"])
