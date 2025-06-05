import socket
import ssl
import time
from datetime import datetime

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
    SSLCheck,
    SSLLabsScan,
    UserAPIKey,
)


class PSIService:
    BASE_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    @staticmethod
    def get_user_api_key(user):
        try:
            key_obj = UserAPIKey.objects.get(user=user, service="psi")
            if not key_obj.key:
                raise Exception(
                    "No Google PSI API key set for your account. Please add it in Settings."
                )
            return key_obj.key
        except UserAPIKey.DoesNotExist:
            raise Exception(
                "No Google PSI API key set for your account. Please add it in Settings."
            )

    @classmethod
    def fetch_report(cls, url, user, strategy="mobile"):
        """
        Fetch PageSpeed Insights report for a given URL and strategy (mobile/desktop)
        """
        api_key = cls.get_user_api_key(user)
        params = {
            "url": url,
            "key": api_key,
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
        mobile_data = cls.fetch_report(url, user, "mobile")
        mobile_report = PSIReport.objects.create(
            group=group,
            page=page,
            fetch_time=fetch_time,
            strategy="mobile",
            raw_json=mobile_data,
            user=user,
        )
        # Fetch and store desktop
        desktop_data = cls.fetch_report(url, user, "desktop")
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
    def fetch_both_reports(cls, url, user):
        """
        Fetch both mobile and desktop reports for a URL
        """
        try:
            mobile_report = cls.fetch_report(url, user, "mobile")
            desktop_report = cls.fetch_report(url, user, "desktop")
            return mobile_report, desktop_report
        except Exception as e:
            raise Exception(f"Error fetching reports: {str(e)}")


class UptimeRobotService:
    BASE_URL = "https://api.uptimerobot.com/v2/"

    @staticmethod
    def get_user_api_key(user):
        try:
            key_obj = UserAPIKey.objects.get(user=user, service="uptimerobot")
            if not key_obj.key:
                raise Exception(
                    "No UptimeRobot API key set for your account. Please add it in Settings."
                )
            return key_obj.key
        except UserAPIKey.DoesNotExist:
            raise Exception(
                "No UptimeRobot API key set for your account. Please add it in Settings."
            )

    @classmethod
    def ensure_monitor(cls, link, user):
        """
        Ensure a monitor exists for the given link. If not, create it and store the monitor ID.
        """
        api_key = cls.get_user_api_key(user)
        if link.uptime_monitor_id:
            return link.uptime_monitor_id
        url = cls.BASE_URL + "newMonitor"
        payload = {
            "api_key": api_key,
            "type": 1,  # HTTP(s) monitor
            "url": link.url,
            "friendly_name": link.title,
        }
        response = requests.post(url, data=payload)
        data = response.json()
        if data.get("stat") == "ok":
            monitor_id = str(data["monitor"]["id"])
            link.uptime_monitor_id = monitor_id
            link.save(update_fields=["uptime_monitor_id"])
            return monitor_id
        else:
            raise Exception(f"Failed to create monitor: {data}")

    @classmethod
    def get_monitor_status(cls, link, user):
        """
        Fetch the current status for the monitor associated with the link, requesting all possible fields.
        """
        api_key = cls.get_user_api_key(user)
        monitor_id = cls.ensure_monitor(link, user)
        url = cls.BASE_URL + "getMonitors"
        payload = {
            "api_key": api_key,
            "monitors": monitor_id,
            "format": "json",
            "logs": 1,
            "response_times": 1,
            "response_times_average": 1,
            "ssl": 1,
            "alert_contacts": 1,
            "custom_uptime_ratios": "1-7-30-60-90",
            "all_time_uptime_ratio": 1,
            "maintenance_windows": 1,
            # Add more fields if supported by the API
        }
        response = requests.post(url, data=payload)
        data = response.json()
        if data.get("stat") == "ok" and data.get("monitors"):
            monitor = data["monitors"][0]
            # Update link with latest status
            link.uptime_last_status = str(monitor.get("status"))
            link.uptime_last_checked = timezone.now()
            link.save(update_fields=["uptime_last_status", "uptime_last_checked"])
            return monitor
        else:
            raise Exception(f"Failed to fetch monitor status: {data}")

    @classmethod
    def get_monitor_details(cls, link, user):
        """
        Fetch full monitor details for the link (same as get_monitor_status, but returns all info).
        """
        return cls.get_monitor_status(link, user)


class SSLService:
    @staticmethod
    def check_certificate(link, user):
        """
        Perform a live SSL certificate inspection for the given link, extract all possible details, and store in SSLCheck.
        """
        import idna

        url = link.url
        hostname = url.split("//")[-1].split("/")[0].split(":")[0]
        port = 443
        warnings = []
        errors = []
        cert = None
        chain_count = 1
        is_self_signed = False
        is_expired = False
        is_weak_signature = False
        is_short_key = False
        san = ""
        ocsp_url = ""
        crl_url = ""
        raw_cert = ""
        subject = ""
        issuer = ""
        serial_number = ""
        version = None
        not_before = None
        not_after = None
        signature_algorithm = ""
        public_key_type = ""
        public_key_bits = None
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    der_cert = ssock.getpeercert(binary_form=True)
                    cert = ssl.DER_cert_to_PEM_cert(der_cert)
                    x509 = ssl._ssl._test_decode_cert(cert)
                    raw_cert = cert
                    subject = str(x509.get("subject", ""))
                    issuer = str(x509.get("issuer", ""))
                    serial_number = str(x509.get("serialNumber", ""))
                    version = x509.get("version")
                    not_before = (
                        datetime.strptime(x509["notBefore"], "%b %d %H:%M:%S %Y %Z")
                        if "notBefore" in x509
                        else None
                    )
                    not_after = (
                        datetime.strptime(x509["notAfter"], "%b %d %H:%M:%S %Y %Z")
                        if "notAfter" in x509
                        else None
                    )
                    san = ",".join(x509.get("subjectAltName", []))
                    signature_algorithm = x509.get("signatureAlgorithm", "")
                    pubkey = x509.get("subjectPublicKeyInfo", {})
                    public_key_type = pubkey.get("algorithm", "")
                    public_key_bits = (
                        pubkey.get("key_size") if "key_size" in pubkey else None
                    )
                    # OCSP/CRL URLs
                    for ext in x509.get("extensions", []):
                        if ext["name"] == "authorityInfoAccess":
                            if "OCSP" in ext["value"]:
                                ocsp_url = ext["value"]["OCSP"]
                        if ext["name"] == "crlDistributionPoints":
                            crl_url = ext["value"]
                    # Chain info (not available via stdlib, so set to 1)
                    # Self-signed check
                    is_self_signed = subject == issuer
                    # Expiry check
                    if not_after and not_after < datetime.utcnow():
                        is_expired = True
                        warnings.append("Certificate is expired.")
                    # Weak signature
                    if "sha1" in signature_algorithm.lower():
                        is_weak_signature = True
                        warnings.append("Weak signature algorithm (SHA1)")
                    # Short key
                    if public_key_bits and public_key_bits < 2048:
                        is_short_key = True
                        warnings.append("Short public key (<2048 bits)")
        except Exception as e:
            errors.append(str(e))
        ssl_check = SSLCheck.objects.create(
            user=user,
            link=link,
            checked_at=datetime.utcnow(),
            subject=subject,
            issuer=issuer,
            serial_number=serial_number,
            version=version,
            not_before=not_before,
            not_after=not_after,
            san=san,
            signature_algorithm=signature_algorithm,
            public_key_type=public_key_type,
            public_key_bits=public_key_bits,
            ocsp_url=ocsp_url,
            crl_url=crl_url,
            chain_count=chain_count,
            is_self_signed=is_self_signed,
            is_expired=is_expired,
            is_weak_signature=is_weak_signature,
            is_short_key=is_short_key,
            warnings="; ".join(warnings),
            errors="; ".join(errors),
            raw_cert=raw_cert,
        )
        return ssl_check


class SSLLabsService:
    API_URL = "https://api.ssllabs.com/api/v3/analyze"
    MAX_POLL = 30  # max polling attempts
    POLL_INTERVAL = 5  # seconds

    @staticmethod
    def run_scan(link, user):
        """
        Start or fetch an SSL Labs scan for the given link, poll if necessary, extract all details, and store in SSLLabsScan.
        """
        hostname = link.url.split("//")[-1].split("/")[0].split(":")[0]
        params = {
            "host": hostname,
            "all": "done",
            "fromCache": "on",
            "ignoreMismatch": "on",
        }
        poll_count = 0
        error = None
        while poll_count < SSLLabsService.MAX_POLL:
            try:
                resp = requests.get(SSLLabsService.API_URL, params=params, timeout=30)
                data = resp.json()
                status = data.get("status")
                if status in ("READY", "ERROR"):
                    break
                elif status in ("IN_PROGRESS", "DNS", "INITIALIZING", "STARTING"):
                    time.sleep(SSLLabsService.POLL_INTERVAL)
                    poll_count += 1
                    continue
                else:
                    error = f"Unexpected scan status: {status}"
                    break
            except Exception as e:
                error = str(e)
                break
        if error:
            scan = SSLLabsScan.objects.create(
                user=user,
                link=link,
                scanned_at=datetime.utcnow(),
                status="ERROR",
                errors=error,
                raw_json=None,
            )
            return scan
        if status == "ERROR":
            scan = SSLLabsScan.objects.create(
                user=user,
                link=link,
                scanned_at=datetime.utcnow(),
                status="ERROR",
                errors=data.get("statusMessage", "Unknown error"),
                raw_json=data,
            )
            return scan
        # Parse endpoints (may be multiple IPs)
        scans = []
        for ep in data.get("endpoints", []):
            details = ep.get("details", {})
            cert = details.get("cert", {})
            scan = SSLLabsScan.objects.create(
                user=user,
                link=link,
                scanned_at=datetime.utcnow(),
                endpoint=ep.get("ipAddress", ""),
                grade=ep.get("grade", ""),
                status=status,
                subject=cert.get("subject", ""),
                issuer=cert.get("issuerLabel", ""),
                serial_number=cert.get("serialNumber", ""),
                not_before=(
                    datetime.utcfromtimestamp(cert["notBefore"] / 1000)
                    if cert.get("notBefore")
                    else None
                ),
                not_after=(
                    datetime.utcfromtimestamp(cert["notAfter"] / 1000)
                    if cert.get("notAfter")
                    else None
                ),
                san=",".join(cert.get("altNames", [])),
                signature_algorithm=cert.get("sigAlg", ""),
                public_key_type=cert.get("keyAlg", ""),
                public_key_bits=cert.get("keySize"),
                ocsp_url=cert.get("ocspUris", [""])[0] if cert.get("ocspUris") else "",
                crl_url=cert.get("crlURIs", [""])[0] if cert.get("crlURIs") else "",
                chain_issues=details.get("chainIssues", ""),
                hsts=details.get("hstsPolicy", {}).get("status", False) == 1,
                hsts_max_age=details.get("hstsPolicy", {}).get("maxAge"),
                hsts_preload=details.get("hstsPreload", False),
                forward_secrecy=details.get("forwardSecrecy", 0) == 2,
                protocols=",".join(
                    [p.get("name", "") for p in details.get("protocols", [])]
                ),
                ciphers=",".join(
                    [
                        c.get("name", "")
                        for c in details.get("suites", {}).get("list", [])
                    ]
                ),
                vulnerabilities=",".join(
                    [k for k, v in details.items() if k.startswith("vuln") and v]
                ),
                warnings="",
                errors="",
                raw_json=ep,
            )
            scans.append(scan)
