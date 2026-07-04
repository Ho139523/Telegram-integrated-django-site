from django.contrib import admin

from wallets.models import (
    Currency,
    Wallet,
    WalletBalance,
    WalletEntry,
    Withdrawal,
)

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "name",
        "symbol",
        "decimals",
        "is_crypto",
        "is_active",
    )

    list_filter = (
        "is_crypto",
        "is_active",
    )

    search_fields = (
        "code",
        "name",
    )

    ordering = (
        "code",
    )




class WalletBalanceInline(admin.TabularInline):

    model = WalletBalance

    extra = 0

    can_delete = False

    readonly_fields = (
        "currency",
        "available",
        "pending",
        "locked",
    )



@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "tel_id",
        "profile",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "profile__tel_id",
        "profile__phone",
        "profile__fname",
        "profile__lname",
        "profile__user__username",
    )

    readonly_fields = (
        "created_at",
        "profile",
    )

    inlines = [
        WalletBalanceInline,
    ]
    def has_add_permission(self, request):
        return False

    @admin.display(ordering="profile__tel_id")
    def tel_id(self, obj):
        return obj.profile.tel_id


@admin.register(WalletBalance)
class WalletBalanceAdmin(admin.ModelAdmin):

    list_display = (
        "wallet",
        "currency",
        "available",
        "pending",
        "locked",
    )

    list_filter = (
        "currency",
    )

    search_fields = (
        "wallet__profile__tel_id",
        "wallet__profile__phone",
        "wallet__profile__fname",
        "wallet__profile__lname",
    )

    readonly_fields = (
        "wallet",
        "currency",
        "available",
        "pending",
        "locked",
    )

    def has_add_permission(self, request):
        return False

@admin.register(WalletEntry)
class WalletEntryAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "wallet",
        "currency",
        "type",
        "amount",
        "created_at",
    )

    list_filter = (
        "type",
        "currency",
        "created_at",
    )

    search_fields = (
        "wallet__profile__tel_id",
        "wallet__profile__phone",
        "wallet__profile__fname",
        "wallet__profile__lname",
        "description",
    )

    readonly_fields = (
        "wallet",
        "currency",
        "type",
        "amount",
        "description",
        "reference_id",
        "created_at",
    )

    date_hierarchy = "created_at"

    ordering = (
        "-created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False



@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "wallet",
        "currency",
        "amount",
        "fee",
        "status",
        "provider",
        "created_at",
    )

    list_filter = (
        "status",
        "currency",
        "provider",
        "created_at",
    )

    search_fields = (
        "wallet__profile__tel_id",
        "wallet__profile__phone",
        "wallet__profile__fname",
        "wallet__profile__lname",
        "external_reference",
    )

    readonly_fields = (
        "wallet",
        "currency",
        "amount",
        "fee",
        "provider",
        "destination",
        "created_at",
    )

    date_hierarchy = "created_at"

    ordering = (
        "-created_at",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
