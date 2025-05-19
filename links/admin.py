from django.contrib import admin
from .models import Link, PSIReport

# Custom admin actions

def clear_links(modeladmin, request, queryset):
    Link.objects.all().delete()
clear_links.short_description = "Delete all links and their reports"

def clear_reports(modeladmin, request, queryset):
    PSIReport.objects.all().delete()
clear_reports.short_description = "Delete all PSI reports (keep links)"

def clear_reports_for_links(modeladmin, request, queryset):
    for link in queryset:
        link.psi_reports.all().delete()
clear_reports_for_links.short_description = "Delete all reports for selected links"

class LinkAdmin(admin.ModelAdmin):
    actions = [clear_links, clear_reports, clear_reports_for_links]
    list_display = ('title', 'url', 'description', 'created_at', 'updated_at')

class PSIReportAdmin(admin.ModelAdmin):
    actions = [clear_reports]
    list_display = ('link', 'created_at')

try:
    admin.site.unregister(Link)
except admin.sites.NotRegistered:
    pass
try:
    admin.site.unregister(PSIReport)
except admin.sites.NotRegistered:
    pass
admin.site.register(Link, LinkAdmin)
admin.site.register(PSIReport, PSIReportAdmin) 