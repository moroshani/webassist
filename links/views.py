import csv
import io
import json

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django_filters import CharFilter, FilterSet
from django.db.models import Avg, Min, Max
from datetime import datetime, timedelta

from .models import Link, Page, PSIReport, PSIReportGroup, UserAPIKey
from .services import PSIService, UptimeRobotService, SSLService, SSLLabsService


class LinkFilter(FilterSet):
    title = CharFilter(lookup_expr="icontains")
    description = CharFilter(lookup_expr="icontains")

    class Meta:
        model = Link
        fields = ["title", "description"]


def home(request):
    return render(request, "links/home.html")


@login_required
def link_list(request):
    # Removed link_list view and related code for the deleted sites page
    pass


@login_required
@require_POST
def fetch_psi_report(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    try:
        group, mobile_report, desktop_report = PSIService.fetch_and_store_report_group(
            link.url, user=request.user
        )
        return JsonResponse(
            {
                "status": "success",
                "message": "PSI reports fetched and stored successfully",
                "group_id": group.id,
                "mobile_report_id": mobile_report.id,
                "desktop_report_id": desktop_report.id,
            }
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@login_required
@require_POST
def delete_psi_report(request, report_id):
    report = get_object_or_404(PSIReport, id=report_id, user=request.user)
    report.delete()
    return JsonResponse({"status": "success"})


@login_required
def psi_reports_list(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    page = Page.objects.filter(url=link.url, user=request.user).first()
    reports = (
        page.psi_reports.filter(user=request.user) if page else PSIReport.objects.none()
    )
    mobile_reports = reports.filter(strategy="mobile")
    desktop_reports = reports.filter(strategy="desktop")
    paginator = Paginator(reports, 10)  # 10 reports per page
    page_number = request.GET.get("page")
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Trend analytics
    trend_start = request.GET.get("trend_start")
    trend_end = request.GET.get("trend_end")
    trend_data = None
    if trend_start and trend_end:
        trend_start_dt = datetime.strptime(trend_start, "%Y-%m-%d")
        trend_end_dt = datetime.strptime(trend_end, "%Y-%m-%d") + timedelta(days=1)
        trend_reports = reports.filter(
            fetch_time__gte=trend_start_dt, fetch_time__lt=trend_end_dt
        )

        def get_stats(qs):
            return {
                "avg": qs.aggregate(
                    performance=Avg("category_scores__performance"),
                    accessibility=Avg("category_scores__accessibility"),
                    best_practices=Avg("category_scores__best_practices"),
                    seo=Avg("category_scores__seo"),
                ),
                "min": qs.aggregate(
                    performance=Min("category_scores__performance"),
                    accessibility=Min("category_scores__accessibility"),
                    best_practices=Min("category_scores__best_practices"),
                    seo=Min("category_scores__seo"),
                ),
                "max": qs.aggregate(
                    performance=Max("category_scores__performance"),
                    accessibility=Max("category_scores__accessibility"),
                    best_practices=Max("category_scores__best_practices"),
                    seo=Max("category_scores__seo"),
                ),
                "points": [
                    {
                        "date": r.fetch_time.strftime("%Y-%m-%d %H:%M"),
                        "performance": (
                            r.category_scores.performance
                            if hasattr(r, "category_scores") and r.category_scores
                            else None
                        ),
                        "accessibility": (
                            r.category_scores.accessibility
                            if hasattr(r, "category_scores") and r.category_scores
                            else None
                        ),
                        "best_practices": (
                            r.category_scores.best_practices
                            if hasattr(r, "category_scores") and r.category_scores
                            else None
                        ),
                        "seo": (
                            r.category_scores.seo
                            if hasattr(r, "category_scores") and r.category_scores
                            else None
                        ),
                        "strategy": r.strategy,
                        "fcp": (
                            r.field_metrics.fcp_ms
                            if hasattr(r, "field_metrics") and r.field_metrics
                            else None
                        ),
                        "lcp": (
                            r.field_metrics.lcp_ms
                            if hasattr(r, "field_metrics") and r.field_metrics
                            else None
                        ),
                        "cls": (
                            r.field_metrics.cls
                            if hasattr(r, "field_metrics") and r.field_metrics
                            else None
                        ),
                        "ttfb": (
                            r.field_metrics.ttfb_ms
                            if hasattr(r, "field_metrics") and r.field_metrics
                            else None
                        ),
                    }
                    for r in qs.order_by("fetch_time")
                ],
            }

        trend_data = {
            "mobile": get_stats(trend_reports.filter(strategy="mobile")),
            "desktop": get_stats(trend_reports.filter(strategy="desktop")),
        }

    # Compare analytics
    compare_start1 = request.GET.get("compare_start1")
    compare_end1 = request.GET.get("compare_end1")
    compare_start2 = request.GET.get("compare_start2")
    compare_end2 = request.GET.get("compare_end2")
    compare_data = None
    if compare_start1 and compare_end1 and compare_start2 and compare_end2:

        def get_period_stats(start, end):
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
            period_reports = reports.filter(
                fetch_time__gte=start_dt, fetch_time__lt=end_dt
            )
            return {
                "mobile": get_stats(period_reports.filter(strategy="mobile")),
                "desktop": get_stats(period_reports.filter(strategy="desktop")),
                "reports": period_reports.order_by("fetch_time"),
            }

        compare_data = {
            "period1": get_period_stats(compare_start1, compare_end1),
            "period2": get_period_stats(compare_start2, compare_end2),
        }

    return render(
        request,
        "links/psi_reports_list.html",
        {
            "link": link,
            "reports": page_obj,
            "mobile_reports": mobile_reports,
            "desktop_reports": desktop_reports,
            "page_obj": page_obj,
            "trend_data": trend_data,
            "trend_start": trend_start,
            "trend_end": trend_end,
            "compare_data": compare_data,
            "compare_start1": compare_start1,
            "compare_end1": compare_end1,
            "compare_start2": compare_start2,
            "compare_end2": compare_end2,
        },
    )


@login_required
def psi_report_detail(request, report_id):
    report = get_object_or_404(PSIReport, id=report_id, user=request.user)
    field_metrics = getattr(report, "field_metrics", None)
    lab_metrics = getattr(report, "lab_metrics", None)
    category_scores = getattr(report, "category_scores", None)
    audits = report.audits.all()
    return render(
        request,
        "links/psi_report_detail.html",
        {
            "report": report,
            "field_metrics": field_metrics,
            "lab_metrics": lab_metrics,
            "category_scores": category_scores,
            "audits": audits,
        },
    )


@login_required
@require_POST
def bulk_delete_links(request):
    data = json.loads(request.body)
    ids = data.get("ids", [])
    Link.objects.filter(id__in=ids, user=request.user).delete()
    return JsonResponse({"status": "success"})


def export_psi_reports(request, link_id):
    link = get_object_or_404(Link, id=link_id)
    reports = link.psi_reports.all().order_by("-created_at")
    data = [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "mobile_report": r.mobile_report,
            "desktop_report": r.desktop_report,
        }
        for r in reports
    ]
    return JsonResponse(data, safe=False)


def export_psi_reports_csv(request, link_id):
    link = get_object_or_404(Link, id=link_id)
    reports = link.psi_reports.all().order_by("-created_at")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="psi_reports_{link_id}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(
        ["id", "created_at", "mobile_performance", "desktop_performance", "link_id"]
    )
    for r in reports:

        def get_score(report):
            try:
                return report["lighthouseResult"]["categories"]["performance"]["score"]
            except Exception:
                return ""

        writer.writerow(
            [
                r.id,
                r.created_at.isoformat(),
                get_score(r.mobile_report),
                get_score(r.desktop_report),
                link.id,
            ]
        )
    return response


def export_links_csv(request):
    links = Link.objects.all().order_by("-created_at")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="links.csv"'
    writer = csv.writer(response)
    writer.writerow(["id", "title", "url", "description", "created_at", "updated_at"])
    for link in links:
        writer.writerow(
            [
                link.id,
                link.title,
                link.url,
                link.description,
                link.created_at.isoformat(),
                link.updated_at.isoformat(),
            ]
        )
    return response


@login_required
@require_POST
def delete_psi_report_group(request, group_id):
    group = get_object_or_404(PSIReportGroup, id=group_id, user=request.user)
    group.delete()
    return JsonResponse({"status": "success"})


@login_required
def export_links_json(request):
    links = Link.objects.filter(user=request.user).order_by("-created_at")
    data = [
        {
            "id": link.id,
            "title": link.title,
            "url": link.url,
            "description": link.description,
            "created_at": link.created_at.isoformat(),
            "updated_at": link.updated_at.isoformat(),
        }
        for link in links
    ]
    return JsonResponse(data, safe=False)


@login_required
@csrf_exempt
@require_POST
def import_links_json(request):
    try:
        if request.content_type == "application/json":
            data = json.loads(request.body)
        else:
            data = json.loads(request.FILES["file"].read().decode())
        created = 0
        for entry in data:
            if "url" in entry and "title" in entry:
                Link.objects.get_or_create(
                    url=entry["url"],
                    defaults={
                        "title": entry.get("title", ""),
                        "description": entry.get("description", ""),
                        "user": request.user,
                    },
                )
                created += 1
        return JsonResponse({"status": "success", "created": created})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@login_required
def dashboard(request):
    links = Link.objects.filter(user=request.user)
    sites_data = []
    for link in links:
        # Always fetch live uptime status
        try:
            UptimeRobotService.get_monitor_status(link, request.user)
        except Exception:
            link.uptime_last_status = "error"
            link.save(update_fields=["uptime_last_status"])
        last_psi = (
            PSIReport.objects.filter(page__url=link.url, user=request.user)
            .order_by("-fetch_time")
            .first()
        )
        # SSL: get latest local and SSL Labs results
        last_ssl = link.ssl_checks.order_by("-checked_at").first()
        last_ssl_labs = link.ssllabs_scans.order_by("-scanned_at").first()
        ssl_status = None
        ssl_last_checked = None
        ssl_expiry = None
        ssl_warnings = None
        ssl_errors = None
        ssl_grade = None
        ssl_labs_status = None
        if last_ssl:
            ssl_status = (
                not last_ssl.is_expired
                and not last_ssl.is_self_signed
                and not last_ssl.errors
            )
            ssl_last_checked = last_ssl.checked_at
            ssl_expiry = last_ssl.not_after
            ssl_warnings = last_ssl.warnings
            ssl_errors = last_ssl.errors
        if last_ssl_labs:
            ssl_grade = last_ssl_labs.grade
            ssl_labs_status = last_ssl_labs.status
        uptime_status = None
        uptime_last_checked = None
        sec_headers_status = None
        sec_headers_last_checked = None
        sites_data.append(
            {
                "link": link,
                "psi_status": (
                    last_psi.raw_json["lighthouseResult"]["categories"]["performance"][
                        "score"
                    ]
                    if last_psi and last_psi.raw_json
                    else None
                ),
                "psi_last_checked": last_psi.fetch_time if last_psi else None,
                "ssl_status": ssl_status,
                "ssl_last_checked": ssl_last_checked,
                "ssl_expiry": ssl_expiry,
                "ssl_warnings": ssl_warnings,
                "ssl_errors": ssl_errors,
                "ssl_grade": ssl_grade,
                "ssl_labs_status": ssl_labs_status,
                "uptime_status": uptime_status,
                "uptime_last_checked": uptime_last_checked,
                "sec_headers_status": sec_headers_status,
                "sec_headers_last_checked": sec_headers_last_checked,
            }
        )
    return render(request, "links/dashboard.html", {"sites_data": sites_data})


@login_required
def site_detail(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    psi_reports = PSIReport.objects.filter(
        page__url=link.url, user=request.user
    ).order_by("-fetch_time")
    # Placeholders for future features
    ssl_results = None
    uptime_results = None
    sec_headers_results = None
    return render(
        request,
        "links/site_detail.html",
        {
            "link": link,
            "psi_reports": psi_reports,
            "ssl_results": ssl_results,
            "uptime_results": uptime_results,
            "sec_headers_results": sec_headers_results,
        },
    )


@login_required
@require_POST
def add_site(request):
    data = json.loads(request.body)
    url = data.get("url")
    title = data.get("title")
    description = data.get("description", "")
    if not url or not title:
        return JsonResponse(
            {"status": "error", "message": "Title and URL are required."}, status=400
        )
    link, created = Link.objects.get_or_create(
        url=url,
        user=request.user,
        defaults={"title": title, "description": description},
    )
    if created:
        messages.success(request, f'Site "{title}" added successfully!')
        return JsonResponse(
            {
                "status": "success",
                "link_id": link.id,
                "title": link.title,
                "url": link.url,
            }
        )
    else:
        return JsonResponse(
            {"status": "error", "message": "Site already exists."}, status=400
        )


@login_required
def profile(request):
    user = request.user
    password_form = PasswordChangeForm(user)
    email_updated = False
    password_updated = False
    if request.method == "POST":
        if "update_email" in request.POST:
            new_email = request.POST.get("email")
            if new_email and new_email != user.email:
                user.email = new_email
                user.save()
                email_updated = True
                messages.success(request, "Email updated successfully.")
        elif "update_password" in request.POST:
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                password_updated = True
                messages.success(request, "Password updated successfully.")
        elif "delete_account" in request.POST:
            user.delete()
            messages.success(request, "Your account has been deleted.")
            return redirect("home")
    return render(
        request,
        "links/profile.html",
        {
            "user": user,
            "password_form": password_form,
            "email_updated": email_updated,
            "password_updated": password_updated,
        },
    )


def root_redirect(request):
    return redirect("dashboard")


@login_required
def features_page(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    # Define available features and their metadata
    features = [
        {
            "name": "PageSpeed Insights",
            "key": "psi",
            "description": "Analyze site performance using Google PSI.",
            "has_history": True,
            "run_url": f"/sites/{link.id}/fetch-psi/",
            "history_url": f"/sites/{link.id}/reports/",
        },
        {
            "name": "Uptime Monitoring",
            "key": "uptime",
            "description": "Check site uptime status using UptimeRobot.",
            "has_history": False,
            "run_url": f"/sites/{link.id}/features/uptime/",
            "history_url": None,
        },
        {
            "name": "SSL Certificate",
            "key": "ssl",
            "description": "Check SSL certificate validity, expiry, and configuration.",
            "has_history": True,
            "run_url": f"/sites/{link.id}/features/ssl/",
            "history_url": f"/sites/{link.id}/features/ssl/history/",
        },
        {
            "name": "SSL Labs Advanced Scan",
            "key": "ssllabs",
            "description": "Run a deep SSL security scan and get a grade (A+ to F) and vulnerabilities.",
            "has_history": True,
            "run_url": f"/sites/{link.id}/features/ssl-labs/",
            "history_url": f"/sites/{link.id}/features/ssl-labs/history/",
        },
        # Add more features here as you implement them
    ]
    return render(
        request, "links/features_page.html", {"link": link, "features": features}
    )


@login_required
def uptime_feature_run(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    try:
        monitor = UptimeRobotService.get_monitor_status(link, request.user)
        # Parse custom uptime ratios
        custom_uptime_ratio = monitor.get("custom_uptime_ratio", "")
        uptime_ratios = []
        if custom_uptime_ratio:
            uptime_ratios = [r.strip() for r in custom_uptime_ratio.split("-")]
        # Last response time
        last_response_time = monitor.get("last_response_time")
        if not last_response_time and monitor.get("response_times"):
            last_response_time = monitor["response_times"][-1]["value"]
        # Alert contacts
        alert_contacts = monitor.get("alert_contacts", [])
        # Maintenance windows
        maintenance_windows = monitor.get("maintenance_windows", [])
        # SSL info
        ssl = monitor.get("ssl")
        # Tags
        tags = monitor.get("tags", "")
        # Raw JSON
        import json

        raw_json = json.dumps(monitor, indent=2)
        context = {
            "link": link,
            "monitor": monitor,
            "uptime_ratios": uptime_ratios,
            "last_response_time": last_response_time,
            "alert_contacts": alert_contacts,
            "maintenance_windows": maintenance_windows,
            "ssl": ssl,
            "tags": tags,
            "raw_json": raw_json,
            "error": None,
        }
    except Exception as e:
        context = {"link": link, "monitor": None, "error": str(e)}
    return render(request, "links/uptime_feature_run.html", context)


@login_required
def uptime_history(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    try:
        monitor = UptimeRobotService.get_monitor_status(link, request.user)
        logs = monitor.get("logs", [])
        # Filtering
        log_type = request.GET.get("type")
        if log_type:
            logs = [log for log in logs if str(log.get("type")) == log_type]
        # Sorting
        sort = request.GET.get("sort", "-datetime")
        reverse = sort.startswith("-")
        sort_key = sort.lstrip("-")
        logs = sorted(logs, key=lambda x: x.get(sort_key), reverse=reverse)
        # Pagination
        page = int(request.GET.get("page", 1))
        per_page = int(request.GET.get("per_page", 20))
        total = len(logs)
        start = (page - 1) * per_page
        end = start + per_page
        logs_page = logs[start:end]
        # Trend analytics
        trend_start = request.GET.get("trend_start")
        trend_end = request.GET.get("trend_end")
        trend_data = None
        if trend_start and trend_end:
            trend_start_dt = datetime.strptime(trend_start, "%Y-%m-%d")
            trend_end_dt = datetime.strptime(trend_end, "%Y-%m-%d") + timedelta(days=1)
            trend_logs = [
                log
                for log in monitor.get("logs", [])
                if log.get("datetime")
                and trend_start <= log["datetime"][:10] <= trend_end
            ]
            # Uptime %: count Up vs. Down events
            up_count = sum(1 for log in trend_logs if log.get("type") == 2)
            down_count = sum(1 for log in trend_logs if log.get("type") == 1)
            total_checks = len(trend_logs)
            uptime_percent = (up_count / total_checks * 100) if total_checks else 0
            # Longest downtime (consecutive Down events)
            longest = 0
            current = 0
            for log in trend_logs:
                if log.get("type") == 1:
                    current += 1
                    if current > longest:
                        longest = current
                else:
                    current = 0
            # Response time stats
            response_times = [
                rt.get("value")
                for log in trend_logs
                for rt in log.get("response_times", [])
                if rt.get("value") is not None
            ]
            min_response = min(response_times) if response_times else None
            max_response = max(response_times) if response_times else None
            avg_response = (
                sum(response_times) / len(response_times) if response_times else None
            )
            # Prepare time series for chart
            points = [
                {"date": log["datetime"][:16], "status": log.get("type")}
                for log in trend_logs
            ]
            trend_data = {
                "uptime_percent": uptime_percent,
                "downtime_events": down_count,
                "longest_downtime": longest,
                "total_checks": total_checks,
                "points": points,
                "logs": trend_logs,
                "min_response": min_response,
                "max_response": max_response,
                "avg_response": avg_response,
            }
        compare_start1 = request.GET.get("compare_start1")
        compare_end1 = request.GET.get("compare_end1")
        compare_start2 = request.GET.get("compare_start2")
        compare_end2 = request.GET.get("compare_end2")
        compare_data = None
        if compare_start1 and compare_end1 and compare_start2 and compare_end2:

            def get_period_stats(start, end):
                start_dt = datetime.strptime(start, "%Y-%m-%d")
                end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
                period_logs = [
                    log
                    for log in monitor.get("logs", [])
                    if log.get("datetime") and start <= log["datetime"][:10] <= end
                ]
                up_count = sum(1 for log in period_logs if log.get("type") == 2)
                down_count = sum(1 for log in period_logs if log.get("type") == 1)
                total_checks = len(period_logs)
                uptime_percent = (up_count / total_checks * 100) if total_checks else 0
                longest = 0
                current = 0
                for log in period_logs:
                    if log.get("type") == 1:
                        current += 1
                        if current > longest:
                            longest = current
                    else:
                        current = 0
                points = [
                    {"date": log["datetime"][:16], "status": log.get("type")}
                    for log in period_logs
                ]
                response_times = [
                    rt.get("value")
                    for log in period_logs
                    for rt in log.get("response_times", [])
                    if rt.get("value") is not None
                ]
                min_response = min(response_times) if response_times else None
                max_response = max(response_times) if response_times else None
                avg_response = (
                    sum(response_times) / len(response_times)
                    if response_times
                    else None
                )
                return {
                    "uptime_percent": uptime_percent,
                    "downtime_events": down_count,
                    "longest_downtime": longest,
                    "total_checks": total_checks,
                    "points": points,
                    "logs": period_logs,
                    "min_response": min_response,
                    "max_response": max_response,
                    "avg_response": avg_response,
                }

            compare_data = {
                "period1": get_period_stats(compare_start1, compare_end1),
                "period2": get_period_stats(compare_start2, compare_end2),
            }
        context = {
            "link": link,
            "logs": logs_page,
            "total": total,
            "page": page,
            "per_page": per_page,
            "log_type": log_type,
            "sort": sort,
            "error": None,
            "trend_data": trend_data,
            "trend_start": trend_start,
            "trend_end": trend_end,
            "compare_data": compare_data,
            "compare_start1": compare_start1,
            "compare_end1": compare_end1,
            "compare_start2": compare_start2,
            "compare_end2": compare_end2,
        }
    except Exception as e:
        context = {"link": link, "logs": [], "error": str(e)}
    return render(request, "links/uptime_history.html", context)


@login_required
def export_uptime_logs_csv(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    monitor = UptimeRobotService.get_monitor_status(link, request.user)
    logs = monitor.get("logs", [])
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="uptime_logs_{link_id}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(["datetime", "type", "reason"])
    for log in logs:
        writer.writerow(
            [
                log.get("datetime"),
                log.get("type"),
                log.get("reason", {}).get("detail", ""),
            ]
        )
    return response


@login_required
def export_uptime_logs_json(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    monitor = UptimeRobotService.get_monitor_status(link, request.user)
    logs = monitor.get("logs", [])
    return JsonResponse(logs, safe=False)


@login_required
def settings_view(request):
    # List of all services and their help info
    SERVICES = [
        {
            "key": "psi",
            "name": "Google PageSpeed Insights",
            "help_url": "https://developers.google.com/speed/docs/insights/v5/get-started",
            "instructions": "Create a project in Google Cloud, enable the PageSpeed Insights API, and generate an API key.",
            "limitations": "Free tier: 25,000 requests/day. Quotas may change.",
        },
        {
            "key": "uptimerobot",
            "name": "UptimeRobot",
            "help_url": "https://uptimerobot.com/dashboard#mySettings",
            "instructions": "Log in to UptimeRobot, go to My Settings, and copy your Main API Key.",
            "limitations": "Free tier: 50 monitors, 5-minute checks. Quotas may change.",
        },
    ]
    user = request.user
    keys = {k.service: k for k in UserAPIKey.objects.filter(user=user)}
    if request.method == "POST":
        for service in SERVICES:
            field = f"key_{service['key']}"
            if field in request.POST:
                value = request.POST.get(field).strip()
                if value:
                    obj, created = UserAPIKey.objects.get_or_create(
                        user=user, service=service["key"]
                    )
                    obj.key = value
                    obj.status = "unknown"
                    obj.save()
                    messages.success(request, f"API key for {service['name']} saved.")
        return redirect("settings")
    return render(
        request,
        "links/settings.html",
        {
            "services": SERVICES,
            "keys": keys,
        },
    )


@login_required
def ssl_labs_feature_run(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    error = None
    scan = None
    if request.method == "POST":
        try:
            scan = SSLLabsService.run_scan(link, request.user)
        except Exception as e:
            error = str(e)
    # Always show the latest SSL Labs scan result
    latest_scan = link.ssllabs_scans.order_by("-scanned_at").first()
    return render(
        request,
        "links/ssl_labs_feature_run.html",
        {
            "link": link,
            "scan": scan or latest_scan,
            "error": error,
        },
    )


@login_required
def ssl_history(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    checks = link.ssl_checks.order_by("-checked_at")
    # Trend analytics
    trend_start = request.GET.get("trend_start")
    trend_end = request.GET.get("trend_end")
    trend_data = None
    if trend_start and trend_end:
        trend_start_dt = datetime.strptime(trend_start, "%Y-%m-%d")
        trend_end_dt = datetime.strptime(trend_end, "%Y-%m-%d") + timedelta(days=1)
        trend_checks = checks.filter(
            checked_at__gte=trend_start_dt, checked_at__lt=trend_end_dt
        )
        trend_data = {
            "min_expiry": trend_checks.aggregate(Min("not_after"))["not_after__min"],
            "max_expiry": trend_checks.aggregate(Max("not_after"))["not_after__max"],
            "count": trend_checks.count(),
            "points": [
                {
                    "date": c.checked_at.strftime("%Y-%m-%d %H:%M"),
                    "expiry": c.not_after,
                    "warnings": c.warnings,
                    "errors": c.errors,
                }
                for c in trend_checks.order_by("checked_at")
            ],
        }
    # Compare analytics
    compare_start1 = request.GET.get("compare_start1")
    compare_end1 = request.GET.get("compare_end1")
    compare_start2 = request.GET.get("compare_start2")
    compare_end2 = request.GET.get("compare_end2")
    compare_data = None
    if compare_start1 and compare_end1 and compare_start2 and compare_end2:

        def get_period_stats(start, end):
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
            period_checks = checks.filter(
                checked_at__gte=start_dt, checked_at__lt=end_dt
            )
            return {
                "min_expiry": period_checks.aggregate(Min("not_after"))[
                    "not_after__min"
                ],
                "max_expiry": period_checks.aggregate(Max("not_after"))[
                    "not_after__max"
                ],
                "count": period_checks.count(),
                "points": [
                    {
                        "date": c.checked_at.strftime("%Y-%m-%d %H:%M"),
                        "expiry": c.not_after,
                        "warnings": c.warnings,
                        "errors": c.errors,
                    }
                    for c in period_checks.order_by("checked_at")
                ],
            }

        compare_data = {
            "period1": get_period_stats(compare_start1, compare_end1),
            "period2": get_period_stats(compare_start2, compare_end2),
        }
    return render(
        request,
        "links/ssl_history.html",
        {
            "link": link,
            "checks": checks,
            "trend_data": trend_data,
            "trend_start": trend_start,
            "trend_end": trend_end,
            "compare_data": compare_data,
            "compare_start1": compare_start1,
            "compare_end1": compare_end1,
            "compare_start2": compare_start2,
            "compare_end2": compare_end2,
        },
    )


@login_required
def ssl_labs_history(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    scans = link.ssllabs_scans.order_by("-scanned_at")
    # Trend analytics
    trend_start = request.GET.get("trend_start")
    trend_end = request.GET.get("trend_end")
    trend_data = None
    if trend_start and trend_end:
        trend_start_dt = datetime.strptime(trend_start, "%Y-%m-%d")
        trend_end_dt = datetime.strptime(trend_end, "%Y-%m-%d") + timedelta(days=1)
        trend_scans = scans.filter(
            scanned_at__gte=trend_start_dt, scanned_at__lt=trend_end_dt
        )
        trend_data = {
            "min_grade": min([s.grade for s in trend_scans if s.grade], default=None),
            "max_grade": max([s.grade for s in trend_scans if s.grade], default=None),
            "count": trend_scans.count(),
            "points": [
                {
                    "date": s.scanned_at.strftime("%Y-%m-%d %H:%M"),
                    "grade": s.grade,
                    "status": s.status,
                    "vulnerabilities": s.vulnerabilities,
                }
                for s in trend_scans.order_by("scanned_at")
            ],
        }
    # Compare analytics
    compare_start1 = request.GET.get("compare_start1")
    compare_end1 = request.GET.get("compare_end1")
    compare_start2 = request.GET.get("compare_start2")
    compare_end2 = request.GET.get("compare_end2")
    compare_data = None
    if compare_start1 and compare_end1 and compare_start2 and compare_end2:

        def get_period_stats(start, end):
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
            period_scans = scans.filter(scanned_at__gte=start_dt, scanned_at__lt=end_dt)
            return {
                "min_grade": min(
                    [s.grade for s in period_scans if s.grade], default=None
                ),
                "max_grade": max(
                    [s.grade for s in period_scans if s.grade], default=None
                ),
                "count": period_scans.count(),
                "points": [
                    {
                        "date": s.scanned_at.strftime("%Y-%m-%d %H:%M"),
                        "grade": s.grade,
                        "status": s.status,
                        "vulnerabilities": s.vulnerabilities,
                    }
                    for s in period_scans.order_by("scanned_at")
                ],
            }

        compare_data = {
            "period1": get_period_stats(compare_start1, compare_end1),
            "period2": get_period_stats(compare_start2, compare_end2),
        }
    return render(
        request,
        "links/ssl_labs_history.html",
        {
            "link": link,
            "scans": scans,
            "trend_data": trend_data,
            "trend_start": trend_start,
            "trend_end": trend_end,
            "compare_data": compare_data,
            "compare_start1": compare_start1,
            "compare_end1": compare_end1,
            "compare_start2": compare_start2,
            "compare_end2": compare_end2,
        },
    )


@login_required
def ssl_feature_run(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    error = None
    ssl_check = None
    if request.method == "POST":
        try:
            ssl_check = SSLService.check_certificate(link, request.user)
        except Exception as e:
            error = str(e)
    # Always show the latest SSLCheck result
    latest_check = link.ssl_checks.order_by("-checked_at").first()
    return render(
        request,
        "links/ssl_feature_run.html",
        {
            "link": link,
            "ssl_check": ssl_check or latest_check,
            "error": error,
        },
    )
