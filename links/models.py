from django.db import models


class Link(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class PSIReport(models.Model):
    link = models.ForeignKey(Link, on_delete=models.CASCADE, related_name='psi_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    mobile_report = models.JSONField()
    desktop_report = models.JSONField()

    def __str__(self):
        return f"PSI Report for {self.link.title} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-created_at'] 