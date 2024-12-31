from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import telbotid

@receiver(post_save, sender=telbotid)
def sync_profile_credit_from_telbot(sender, instance, **kwargs):
    from accounts.models import ProfileModel

    # از profile مطمئن شو
    if not instance.profile:
        return

    # بررسی اینکه پروفایل در حال sync نباشد
    if hasattr(instance.profile, '_syncing'):
        return

    # تنظیم فیلد _syncing در پروفایل
    instance.profile._syncing = True
    
    # اگر اعتبار پروفایل با اعتبار telbot فرق داشت، پروفایل را به‌روزرسانی کن
    if instance.profile.credit != instance.credit:
        instance.profile.credit = instance.credit
        instance.profile.save()

    # حذف _syncing بعد از عملیات
    del instance.profile._syncing