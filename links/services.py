import requests
from django.conf import settings
from django.utils import timezone

from .models import (
    Audit,
    CategoryScores,
    FieldMetrics,
    LabMetrics,
    Page,
    PSIReport,
    PSIReportGroup,
)


class PSIService:
    API_KEY = settings.PSI_API_KEY
    BASE_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    @classmethod
    def fetch_report(cls, url, strategy="mobile"):
        """
        Fetch PageSpeed Insights report for a given URL and strategy (mobile/desktop)
        """
        params = {
            "url": url,
            "key": cls.API_KEY,
            "strategy": strategy,
            "category": ["performance", "accessibility", "best-practices", "seo"],
        }

        try:
            response = requests.get(cls.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise Exception(
                    "Google API quota exceeded. Please try again later or check your API usage in the Google Cloud Console."
                )
            elif e.response.status_code == 400:
                raise Exception(
                    "Invalid URL or request parameters. Please check the URL and try again."
                )
            elif e.response.status_code == 403:
                raise Exception(
                    "Access forbidden: Your API key may be invalid, restricted, or over quota. Check your Google Cloud Console settings."
                )
            else:
                raise Exception(
                    f"Google API HTTP error: {e.response.status_code} {e.response.reason}. Details: {e.response.text}"
                )
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while fetching PSI report: {str(e)}")

    @classmethod
    def fetch_and_store_report_group(cls, url, user):
        """
        Fetch both mobile and desktop PSI reports, create a group, and store all relevant data.
        """
        fetch_time = timezone.now()
        # Get or create Page
        page, _ = Page.objects.get_or_create(url=url, user=user)
        # Create group
        group = PSIReportGroup.objects.create(
            page=page, fetch_time=fetch_time, user=user
        )
        # Fetch and store mobile
        mobile_data = cls.fetch_report(url, "mobile")
        mobile_report = PSIReport.objects.create(
            group=group,
            page=page,
            fetch_time=fetch_time,
            strategy="mobile",
            raw_json=mobile_data,
            user=user,
        )
        # Fetch and store desktop
        desktop_data = cls.fetch_report(url, "desktop")
        desktop_report = PSIReport.objects.create(
            group=group,
            page=page,
            fetch_time=fetch_time,
            strategy="desktop",
            raw_json=desktop_data,
            user=user,
        )
        # Store metrics and audits for both
        for psi_report, data in [
            (mobile_report, mobile_data),
            (desktop_report, desktop_data),
        ]:
            # --- Field Metrics ---
            field = data.get("loadingExperience", {})
            metrics = field.get("metrics", {})
            has_data = bool(metrics)
            FieldMetrics.objects.create(
                psi_report=psi_report,
                fcp_ms=metrics.get("FIRST_CONTENTFUL_PAINT_MS", {}).get("percentile"),
                lcp_ms=metrics.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("percentile"),
                fid_ms=metrics.get("FIRST_INPUT_DELAY_MS", {}).get("percentile"),
                inp_ms=metrics.get("INTERACTION_TO_NEXT_PAINT", {}).get("percentile"),
                cls=metrics.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("percentile"),
                ttfb_ms=metrics.get("EXPERIMENTAL_TIME_TO_FIRST_BYTE", {}).get(
                    "percentile"
                ),
                overall_category=field.get("overall_category"),
                has_data=has_data,
            )
            # --- Lab Metrics ---
            lhr = data.get("lighthouseResult", {})
            audits = lhr.get("audits", {})
            LabMetrics.objects.create(
                psi_report=psi_report,
                fcp_s=audits.get("first-contentful-paint", {}).get("numericValue"),
                lcp_s=audits.get("largest-contentful-paint", {}).get("numericValue"),
                speed_index_s=audits.get("speed-index", {}).get("numericValue"),
                tti_s=audits.get("interactive", {}).get("numericValue"),
                tbt_ms=audits.get("total-blocking-time", {}).get("numericValue"),
                cls=audits.get("cumulative-layout-shift", {}).get("numericValue"),
                performance_score=lhr.get("categories", {})
                .get("performance", {})
                .get("score"),
            )
            # --- Category Scores ---
            categories = lhr.get("categories", {})
            CategoryScores.objects.create(
                psi_report=psi_report,
                performance=categories.get("performance", {}).get("score"),
                accessibility=categories.get("accessibility", {}).get("score"),
                best_practices=categories.get("best-practices", {}).get("score"),
                seo=categories.get("seo", {}).get("score"),
            )
            # --- Audits ---
            for cat_key, cat in categories.items():
                for ref in cat.get("auditRefs", []):
                    audit_key = ref.get("id")
                    audit = audits.get(audit_key, {})
                    Audit.objects.create(
                        psi_report=psi_report,
                        category=cat_key,
                        audit_key=audit_key,
                        title=audit.get("title", ""),
                        description=audit.get("description", ""),
                        score=audit.get("score"),
                        score_display_mode=audit.get("scoreDisplayMode"),
                        display_value=audit.get("displayValue"),
                        details=audit.get("details"),
                    )
        return group, mobile_report, desktop_report

    @classmethod
    def fetch_both_reports(cls, url):
        """
        Fetch both mobile and desktop reports for a URL
        """
        try:
            mobile_report = cls.fetch_report(url, "mobile")
            desktop_report = cls.fetch_report(url, "desktop")
            return mobile_report, desktop_report
        except Exception as e:
            raise Exception(f"Error fetching reports: {str(e)}")
