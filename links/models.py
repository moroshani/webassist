from typing import Optional

from django.contrib.auth.models import User
from django.db import models


class Link(models.Model):
    """A website link tracked by the user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='links')
    title: str = models.CharField(max_length=255)
    url: str = models.URLField(unique=True)
    description: str = models.TextField(blank=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """String representation of the link."""
        return self.title

    class Meta:
        ordering = ['-created_at']


class Page(models.Model):
    """A page for which PSI reports are tracked."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pages')
    url: str = models.URLField(unique=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """String representation of the page."""
        return self.url


class PSIReportGroup(models.Model):
    """A group of PSI reports (mobile/desktop) for a page at a specific time."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psi_report_groups')
    page: Page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='psi_report_groups')
    fetch_time: models.DateTimeField = models.DateTimeField()

    def __str__(self) -> str:
        """String representation of the report group."""
        return f"PSI Report Group for {self.page.url if self.page else 'Unknown'} - {self.fetch_time.strftime('%Y-%m-%d %H:%M') if self.fetch_time else 'No Date'}"


class PSIReport(models.Model):
    """A single PSI report (mobile or desktop) for a page."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psi_reports')
    group: Optional[PSIReportGroup] = models.ForeignKey('PSIReportGroup', on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    page: Optional[Page] = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='psi_reports', blank=True, null=True)
    fetch_time: Optional[models.DateTimeField] = models.DateTimeField(blank=True, null=True)
    strategy: Optional[str] = models.CharField(max_length=16, choices=[('mobile', 'Mobile'), ('desktop', 'Desktop')], blank=True, null=True)
    raw_json: Optional[dict] = models.JSONField(blank=True, null=True)

    def __str__(self) -> str:
        """String representation of the PSI report."""
        return f"PSI Report for {self.page.url if self.page else 'Unknown'} - {self.fetch_time.strftime('%Y-%m-%d %H:%M') if self.fetch_time else 'No Date'}"

    class Meta:
        ordering = ['-fetch_time']


class FieldMetrics(models.Model):
    """Field metrics from PSI (real user data)."""
    psi_report: PSIReport = models.OneToOneField(PSIReport, on_delete=models.CASCADE, related_name='field_metrics')
    fcp_ms: Optional[float] = models.FloatField(null=True)
    lcp_ms: Optional[float] = models.FloatField(null=True)
    fid_ms: Optional[float] = models.FloatField(null=True)
    inp_ms: Optional[float] = models.FloatField(null=True)
    cls: Optional[float] = models.FloatField(null=True)
    ttfb_ms: Optional[float] = models.FloatField(null=True)
    overall_category: Optional[str] = models.CharField(max_length=32, null=True)
    has_data: bool = models.BooleanField(default=False)


class LabMetrics(models.Model):
    """Lab metrics from PSI (simulated data)."""
    psi_report: PSIReport = models.OneToOneField(PSIReport, on_delete=models.CASCADE, related_name='lab_metrics')
    fcp_s: Optional[float] = models.FloatField(null=True)
    lcp_s: Optional[float] = models.FloatField(null=True)
    speed_index_s: Optional[float] = models.FloatField(null=True)
    tti_s: Optional[float] = models.FloatField(null=True)
    tbt_ms: Optional[float] = models.FloatField(null=True)
    cls: Optional[float] = models.FloatField(null=True)
    performance_score: Optional[float] = models.FloatField(null=True)


class CategoryScores(models.Model):
    """Category scores from PSI (performance, accessibility, etc)."""
    psi_report: PSIReport = models.OneToOneField(PSIReport, on_delete=models.CASCADE, related_name='category_scores')
    performance: Optional[float] = models.FloatField(null=True)
    accessibility: Optional[float] = models.FloatField(null=True)
    best_practices: Optional[float] = models.FloatField(null=True)
    seo: Optional[float] = models.FloatField(null=True)


class Audit(models.Model):
    """Detailed audit results from PSI."""
    psi_report: PSIReport = models.ForeignKey(PSIReport, on_delete=models.CASCADE, related_name='audits')
    category: str = models.CharField(max_length=32)
    audit_key: str = models.CharField(max_length=64)
    title: str = models.CharField(max_length=256)
    description: str = models.TextField()
    score: Optional[float] = models.FloatField(null=True)
    score_display_mode: Optional[str] = models.CharField(max_length=32, null=True)
    display_value: Optional[str] = models.CharField(max_length=256, null=True)
    details: Optional[dict] = models.JSONField(null=True) 