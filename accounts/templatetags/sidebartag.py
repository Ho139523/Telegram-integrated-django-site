from django import template
from accounts.models import User

register = template.Library()


@register.inclusion_tag("registration/tags/sidebar_tag.html", takes_context=True)
def SidebarTag(context, **kwargs):
    sidebar=(
    ("dashboard", "dashboard"),
    ("billing", "receipt_long"),
    ("notifications", "notifications"),
    ("profile", "person"),
    ("Change Password", "key"),
    )
    data = {
    "sidebar": [(item, logo) for item, logo in sidebar],
    "view": kwargs.get("view", context['view']),  # Default to "Profile" if not provided
    "app_name": kwargs.get("app_name", "accounts:"),
    "request": context['request'],
    "username": kwargs.get("username", context['request'].user.username),
    "user": User.objects.get(username=kwargs.get("username", context['request'].user.username)),
    }
    
    return data