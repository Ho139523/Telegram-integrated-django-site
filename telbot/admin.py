from django.contrib import admin
from .models import telbotid


class telbotidAdmin(admin.ModelAdmin):
    list_display = ('tel_id', 'credit')  # Fields to show in the list view
    search_fields = ('tel_id',)  # Enable search by these fields
    ordering = ('credit',)  # Default ordering
    list_editable = ('credit',)  # Fields editable directly in the list view

admin.site.register(telbotid, telbotidAdmin)


