from rest_framework import permissions
from accounts.models import ProfileModel
from products.models import Store

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    اگر آبجکت فیلدی به نام `profile` یا `user` دارد آن را بررسی می‌کند.
    برای مثال ProfileModel, Product (که profile دارد) و غیره.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # اگر مستقیم profile دارد
        if hasattr(obj, 'profile'):
            return obj.profile.user == request.user if obj.profile and obj.profile.user else False
        # اگر owner دارد مثل Store.owner (owner یک ProfileModel است)
        if hasattr(obj, 'owner'):
            owner = getattr(obj, 'owner')
            return owner.user == request.user if owner and owner.user else False
        # اگر خود آبجکت user است
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        return False

class IsStoreOwner(permissions.BasePermission):
    """
    برای ViewSet های که Store-specific هستند.
    چک می‌کند کاربر صاحب store باشد.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # obj می‌تواند Store باشد یا مدل مرتبط با store که فیلد store دارد
        if hasattr(obj, 'store'):
            return obj.store.owner.user == request.user
        if isinstance(obj, Store):
            return obj.owner.user == request.user
        return False
