from django.contrib import admin
from .models import Link

@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'created_at', 'updated_at')
    search_fields = ('title', 'url', 'description')
    list_filter = ('created_at', 'updated_at') 