from django.contrib import admin

from .models import (
    Audit,
    CategoryScores,
    FieldMetrics,
    LabMetrics,
    Link,
    Page,
    PSIReport,
)

# Custom admin actions

def clear_links(modeladmin, request, queryset):
    Link.objects.all().delete()
clear_links.short_description = "Delete all links"

def export_links_csv(modeladmin, request, queryset):
    import csv

    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=links.csv'
    writer = csv.writer(response)
    writer.writerow(['id', 'title', 'url', 'description', 'created_at', 'updated_at'])
    for link in queryset:
        writer.writerow([link.id, link.title, link.url, link.description, link.created_at, link.updated_at])
    return response
export_links_csv.short_description = "Export selected links as CSV"

class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'description', 'created_at', 'updated_at')
    search_fields = ('title', 'url', 'description')
    list_filter = ('created_at', 'updated_at')
    actions = [clear_links, export_links_csv]

class PSIReportAdmin(admin.ModelAdmin):
    list_display = ('page', 'strategy', 'fetch_time')
    search_fields = ('page__url', 'strategy')
    list_filter = ('strategy', 'fetch_time')

try:
    admin.site.unregister(Link)
except admin.sites.NotRegistered:
    pass
try:
    admin.site.unregister(PSIReport)
except admin.sites.NotRegistered:
    pass
admin.site.register(Link, LinkAdmin)
admin.site.register(Page)
admin.site.register(PSIReport, PSIReportAdmin)
admin.site.register(FieldMetrics)
admin.site.register(LabMetrics)
admin.site.register(CategoryScores)
admin.site.register(Audit) 