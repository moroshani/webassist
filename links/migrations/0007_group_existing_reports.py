from django.db import migrations

def group_existing_reports(apps, schema_editor):
    PSIReport = apps.get_model('links', 'PSIReport')
    PSIReportGroup = apps.get_model('links', 'PSIReportGroup')
    Page = apps.get_model('links', 'Page')
    from django.db.models import F

    # Find all unique (page, fetch_time) pairs
    pairs = (
        PSIReport.objects
        .values('page', 'fetch_time')
        .distinct()
        .exclude(page=None)
        .exclude(fetch_time=None)
    )
    for pair in pairs:
        page_id = pair['page']
        fetch_time = pair['fetch_time']
        # Create group
        group = PSIReportGroup.objects.create(page_id=page_id, fetch_time=fetch_time)
        # Assign all reports with this page and fetch_time to the group
        PSIReport.objects.filter(page_id=page_id, fetch_time=fetch_time).update(group=group)

class Migration(migrations.Migration):
    dependencies = [
        ('links', '0006_psireportgroup_psireport_group'),
    ]
    operations = [
        migrations.RunPython(group_existing_reports, reverse_code=migrations.RunPython.noop),
    ] 