from typing import Optional

from django.contrib.auth.models import User
from django.db import models
from django_cryptography.fields import encrypt


class Link(models.Model):
    """A website link tracked by the user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="links")
    title = models.CharField(max_length=255)
    url = models.URLField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # UptimeRobot integration fields
    uptime_monitor_id = models.CharField(max_length=32, blank=True, null=True)
    uptime_last_status = models.CharField(max_length=32, blank=True, null=True)
    uptime_last_checked = models.DateTimeField(blank=True, null=True)

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
    fetch_time = models.DateTimeField(blank=True, null=True)
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


class UserAPIKey(models.Model):
    SERVICE_CHOICES = [
        ("psi", "Google PageSpeed Insights"),
        ("uptimerobot", "UptimeRobot"),
        # Add more as needed
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")
    service = models.CharField(max_length=32, choices=SERVICE_CHOICES)
    key = encrypt(models.CharField(max_length=255))
    status = models.CharField(max_length=32, blank=True, null=True)
    usage = models.IntegerField(blank=True, null=True)
    last_checked = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("user", "service")

    def __str__(self):
        return f"{self.user.username} - {self.get_service_display()}"


class SSLCheck(models.Model):
    """Result of a local SSL certificate check for a site."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ssl_checks")
    link = models.ForeignKey(Link, on_delete=models.CASCADE, related_name="ssl_checks")
    checked_at = models.DateTimeField(auto_now_add=True)
    # Certificate details
    subject = models.TextField()
    issuer = models.TextField()
    serial_number = models.CharField(max_length=128)
    version = models.IntegerField(null=True)
    not_before = models.DateTimeField()
    not_after = models.DateTimeField()
    san = models.TextField(blank=True)  # comma-separated
    signature_algorithm = models.CharField(max_length=128, blank=True)
    public_key_type = models.CharField(max_length=64, blank=True)
    public_key_bits = models.IntegerField(null=True)
    ocsp_url = models.TextField(blank=True)
    crl_url = models.TextField(blank=True)
    # Chain info
    chain_count = models.IntegerField(default=1)
    is_self_signed = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)
    is_weak_signature = models.BooleanField(default=False)
    is_short_key = models.BooleanField(default=False)
    # Warnings and errors
    warnings = models.TextField(blank=True)
    errors = models.TextField(blank=True)
    # Raw cert (PEM or DER, optional)
    raw_cert = models.TextField(blank=True)

    class Meta:
        ordering = ["-checked_at"]


class SSLLabsScan(models.Model):
    """Result of an SSL Labs advanced scan for a site."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="ssllabs_scans"
    )
    link = models.ForeignKey(
        Link, on_delete=models.CASCADE, related_name="ssllabs_scans"
    )
    scanned_at = models.DateTimeField(auto_now_add=True)
    endpoint = models.CharField(max_length=255, blank=True)  # IP or hostname
    grade = models.CharField(max_length=4, blank=True)
    status = models.CharField(max_length=64, blank=True)
    # Certificate details
    subject = models.TextField(blank=True)
    issuer = models.TextField(blank=True)
    serial_number = models.CharField(max_length=128, blank=True)
    not_before = models.DateTimeField(null=True)
    not_after = models.DateTimeField(null=True)
    san = models.TextField(blank=True)
    signature_algorithm = models.CharField(max_length=128, blank=True)
    public_key_type = models.CharField(max_length=64, blank=True)
    public_key_bits = models.IntegerField(null=True)
    ocsp_url = models.TextField(blank=True)
    crl_url = models.TextField(blank=True)
    chain_issues = models.TextField(blank=True)
    # Security features
    hsts = models.BooleanField(default=False)
    hsts_max_age = models.IntegerField(null=True)
    hsts_preload = models.BooleanField(default=False)
    forward_secrecy = models.BooleanField(default=False)
    protocols = models.TextField(blank=True)  # comma-separated
    ciphers = models.TextField(blank=True)  # comma-separated
    vulnerabilities = models.TextField(blank=True)
    # Warnings and errors
    warnings = models.TextField(blank=True)
    errors = models.TextField(blank=True)
    # Full raw JSON
    raw_json = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["-scanned_at"]
