from django.db import models

class LedgerEntry(models.Model):

    profile = models.ForeignKey(
        "accounts.ProfileModel",
        on_delete=models.CASCADE
    )

    debit = models.BigIntegerField(default=0)
    credit = models.BigIntegerField(default=0)

    reference_type = models.CharField(max_length=50)
    reference_id = models.UUIDField()

    created_at = models.DateTimeField(auto_now_add=True)

