from typing import Optional

from django.contrib.auth.models import User
from django.db import models


class Link(models.Model):
    """A website link tracked by the user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="links")
    title = models.CharField(max_length=255)
    url = models.URLField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """String representation of the link."""
        return self.title

    class Meta:
        ordering = ["-created_at"]


class Page(models.Model):
    """A page for which PSI reports are tracked."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pages")
    url = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """String representation of the page."""
        return self.url


class PSIReportGroup(models.Model):
    """A group of PSI reports (mobile/desktop) for a page at a specific time."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="psi_report_groups"
    )
    page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name="psi_report_groups"
    )
    fetch_time = models.DateTimeField()

    def __str__(self) -> str:
        """String representation of the report group."""
        return f"PSI Report Group for {self.page.url if self.page else 'Unknown'} - {self.fetch_time.strftime('%Y-%m-%d %H:%M') if self.fetch_time else 'No Date'}"


class PSIReport(models.Model):
    """A single PSI report (mobile or desktop) for a page."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="psi_reports")
    group = models.ForeignKey(
        "PSIReportGroup",
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True,
    )
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name="psi_reports",
        blank=True,
        null=True,
    )
    fetch_time = models.DateTimeField(
        blank=True, null=True
    )
    strategy = models.CharField(
        max_length=16,
        choices=[("mobile", "Mobile"), ("desktop", "Desktop")],
        blank=True,
        null=True,
    )
    raw_json = models.JSONField(blank=True, null=True)

    def __str__(self) -> str:
        """String representation of the PSI report."""
        return f"PSI Report for {self.page.url if self.page else 'Unknown'} - {self.fetch_time.strftime('%Y-%m-%d %H:%M') if self.fetch_time else 'No Date'}"

    class Meta:
        ordering = ["-fetch_time"]


class FieldMetrics(models.Model):
    """Field metrics from PSI (real user data)."""

    psi_report = models.OneToOneField(
        PSIReport, on_delete=models.CASCADE, related_name="field_metrics"
    )
    fcp_ms = models.FloatField(null=True)
    lcp_ms = models.FloatField(null=True)
    fid_ms = models.FloatField(null=True)
    inp_ms = models.FloatField(null=True)
    cls = models.FloatField(null=True)
    ttfb_ms = models.FloatField(null=True)
    overall_category = models.CharField(max_length=32, null=True)
    has_data = models.BooleanField(default=False)


class LabMetrics(models.Model):
    """Lab metrics from PSI (simulated data)."""

    psi_report = models.OneToOneField(
        PSIReport, on_delete=models.CASCADE, related_name="lab_metrics"
    )
    fcp_s = models.FloatField(null=True)
    lcp_s = models.FloatField(null=True)
    speed_index_s = models.FloatField(null=True)
    tti_s = models.FloatField(null=True)
    tbt_ms = models.FloatField(null=True)
    cls = models.FloatField(null=True)
    performance_score = models.FloatField(null=True)


class CategoryScores(models.Model):
    """Category scores from PSI (performance, accessibility, etc)."""

    psi_report = models.OneToOneField(
        PSIReport, on_delete=models.CASCADE, related_name="category_scores"
    )
    performance = models.FloatField(null=True)
    accessibility = models.FloatField(null=True)
    best_practices = models.FloatField(null=True)
    seo = models.FloatField(null=True)


class Audit(models.Model):
    """Detailed audit results from PSI."""

    psi_report = models.ForeignKey(
        PSIReport, on_delete=models.CASCADE, related_name="audits"
    )
    category = models.CharField(max_length=32)
    audit_key = models.CharField(max_length=64)
    title = models.CharField(max_length=256)
    description = models.TextField()
    score = models.FloatField(null=True)
    score_display_mode = models.CharField(max_length=32, null=True)
    display_value = models.CharField(max_length=256, null=True)
    details = models.JSONField(null=True)
