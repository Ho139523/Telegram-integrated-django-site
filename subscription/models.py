from django.db import models, transaction
from accounts.models import User, ProfileModel
from django.core.exceptions import ValidationError
import os
import hashlib
from django.utils.text import slugify
import pycountry



from django.utils import timezone
from datetime import timedelta


class Plan(models.Model):

    PLAN_TYPES = [
        ('basic', 'پایه'),
        ('advanced', 'پیشرفته'),
        ('professional', 'حرفه‌ای'),
    ]

    code = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.get_code_display()


class Feature(models.Model):

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class PlanFeature(models.Model):

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="features")
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    value = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('plan', 'feature')


class PlanPrice(models.Model):

    DURATION_CHOICES = [
        (1, "1 ماه"),
        (3, "3 ماه"),
        (6, "6 ماه"),
        (12, "12 ماه"),
    ]

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="prices")
    months = models.PositiveIntegerField(choices=DURATION_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('plan', 'months')



class Coupon(models.Model):

    DISCOUNT_TYPE = [
        ('percent', 'درصدی'),
        ('fixed', 'مبلغ ثابت'),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    max_usage = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)

    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()

    is_active = models.BooleanField(default=True)

    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            self.used_count < self.max_usage
        )



class Subscription(models.Model):

    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'فعال'),
        ('expired', 'منقضی'),
        ('canceled', 'لغو شده'),
    ]

    store = models.OneToOneField('products.Store', on_delete=models.CASCADE, related_name="subscription")
    
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)

    start_date = models.DateTimeField(auto_now_add=True)

    end_date = models.DateTimeField(db_index=True)

    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='trial', db_index=True)

    is_auto_renew = models.BooleanField(default=False)

    zarinpal_token = models.CharField(max_length=255, blank=True, null=True)

    pending_plan = models.ForeignKey(Plan,null=True,blank=True,related_name="pending_subscriptions",on_delete=models.SET_NULL)


    @property
    def is_valid(self):
        return self.end_date > timezone.now()


    def is_active(self):
        return self.status in ['trial', 'active'] and self.end_date > timezone.now()

    def days_left(self):
        if self.end_date > timezone.now():
            return (self.end_date - timezone.now()).days
        return 0

    def cancel(self):
        self.status = 'canceled'
        self.save()

    class Meta:
        indexes = [
            models.Index(fields=["status", "end_date"]),
        ]

    def check_and_expire(self):
        if self.status in ['trial', 'active'] and self.end_date <= timezone.now():
            self.status = 'expired'
            self.save(update_fields=['status'])




class SubscriptionInvoice(models.Model):

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    plan_price = models.ForeignKey(PlanPrice, on_delete=models.SET_NULL, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)

    is_paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


class Payment(models.Model):

    invoice = models.ForeignKey(SubscriptionInvoice, on_delete=models.CASCADE)

    authority = models.CharField(max_length=100, blank=True)
    ref_id = models.CharField(max_length=100, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    card_pan = models.CharField(max_length=20, blank=True)
    card_hash = models.CharField(max_length=100, blank=True)



class SubscriptionUsage(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="usages")
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    used_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("subscription", "feature")

    def increment(self, amount=1):
        self.used_count += amount
        self.save(update_fields=["used_count"])
