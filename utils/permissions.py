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





from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from django.db import IntegrityError
import hmac
import hashlib
import json




# ================================================
# Signature Permission (بدون نیاز به JWT)
# ================================================

class BotSignaturePermission(BasePermission):
    """
    Permission for bot requests using HMAC-SHA256 signature
    All CRUD operations require valid signature
    """
    
    BOT_SECRET = "9cb87c53630243ab6244c20321c00acae9ee896624010ad1b81dd16c89edee91"
    
    def has_permission(self, request, view):
        # Get signature headers
        timestamp = request.headers.get('X-Bot-Timestamp')
        signature = request.headers.get('X-Bot-Signature')
        
        if not timestamp or not signature:
            logger.warning("Missing signature headers")
            return False
        
        # Get request body (GET requests may have no body)
        body_bytes = request.body or b'{}'
        
        # Verify signature
        msg = timestamp.encode() + b"." + body_bytes
        expected_signature = hmac.new(
            self.BOT_SECRET.encode(), 
            msg, 
            hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if not is_valid:
            logger.warning(f"Invalid signature for {request.path}")
        
        return is_valid