from django.db import migrations, models
import django_cryptography.fields
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("links", "0002_link_uptime_last_checked_link_uptime_last_status_and_more"),
    ]
    operations = [
        migrations.CreateModel(
            name="UserAPIKey",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "service",
                    models.CharField(
                        max_length=32,
                        choices=[
                            ("psi", "Google PageSpeed Insights"),
                            ("uptimerobot", "UptimeRobot"),
                        ],
                    ),
                ),
                (
                    "key",
                    django_cryptography.fields.encrypt(
                        models.CharField(max_length=255)
                    ),
                ),
                ("status", models.CharField(blank=True, max_length=32, null=True)),
                ("usage", models.IntegerField(blank=True, null=True)),
                ("last_checked", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="api_keys",
                        to="auth.user",
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "service")},
            },
        ),
    ]
