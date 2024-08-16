from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


UserAdmin.list_display += ("is_special_user",)
UserAdmin.fieldsets[2][1]["fields"]= (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "special_user",
                    "groups",
                    "user_permissions",
                )
admin.site.register(User, UserAdmin)