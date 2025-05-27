import csv
import io
import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User # Should be settings.AUTH_USER_MODEL
from django.conf import settings # Import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Avg, Max, Min, OuterRef, Subquery, F, DateTimeField, FloatField, CharField, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from django_filters import CharFilter, FilterSet

from .models import Link, Page, PSIReport, PSIReportGroup, UserAPIKey, SSLCheck, SSLLabsScan
from .services import PSIService, SSLLabsService, SSLService, UptimeRobotService
from .forms import APIKeyForm
from .analytics_utils import get_trend_data_for_queryset, get_compare_data_for_queryset, get_trend_data_for_logs, get_compare_data_for_logs


class LinkFilter(FilterSet):
    title = CharFilter(lookup_expr="icontains")
    description = CharFilter(lookup_expr="icontains")

    class Meta:
        model = Link
        fields = ["title", "description"]


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
    # This function seems to delete a single PSIReport, but the UI seems to want to delete groups.
    # Consider if this is still needed or if delete_psi_report_group covers all use cases.
    report = get_object_or_404(PSIReport, id=report_id, user=request.user)
    report.delete()
    return JsonResponse({"status": "success"})


@login_required
def psi_reports_list(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    page_obj_db = Page.objects.filter(url=link.url, user=request.user).first() # Renamed to avoid conflict
    
    reports_qs = PSIReport.objects.none()
    if page_obj_db:
        reports_qs = page_obj_db.psi_reports.filter(user=request.user).select_related('category_scores', 'group')


    # Server-side filtering
    start_date_str = request.GET.get('startDate')
    end_date_str = request.GET.get('endDate')
    min_score_str = request.GET.get('minScore')
    max_score_str = request.GET.get('maxScore')
    search_query = request.GET.get('search') # Renamed

    if start_date_str:
        reports_qs = reports_qs.filter(fetch_time__date__gte=start_date_str)
    if end_date_str:
        reports_qs = reports_qs.filter(fetch_time__date__lte=end_date_str)
    if min_score_str:
        try:
            min_score_val = float(min_score_str)
            reports_qs = reports_qs.filter(category_scores__performance__gte=min_score_val)
        except ValueError:
            pass # Or handle error
    if max_score_str:
        try:
            max_score_val = float(max_score_str)
            reports_qs = reports_qs.filter(category_scores__performance__lte=max_score_val)
        except ValueError:
            pass # Or handle error
    if search_query: # Use renamed variable
        reports_qs = reports_qs.filter(
            Q(page__url__icontains=search_query) |
            Q(page__user__username__icontains=search_query) # Consider if user search is needed here
        )
    
    mobile_reports = reports_qs.filter(strategy="mobile").order_by('-fetch_time')
    desktop_reports = reports_qs.filter(strategy="desktop").order_by('-fetch_time')
    
    # Pagination - apply to one of the report types or a combined list if needed
    # For now, let's assume pagination is for mobile reports as an example, or adjust as needed
    paginator = Paginator(mobile_reports, 10)
    page_number = request.GET.get("page")
    try:
        page_obj_paginated = paginator.page(page_number) # Renamed to avoid conflict
    except PageNotAnInteger:
        page_obj_paginated = paginator.page(1)
    except EmptyPage:
        page_obj_paginated = paginator.page(paginator.num_pages)

    # Trend analytics
    trend_data = get_trend_data_for_queryset(reports_qs, 'fetch_time', group_by_field='strategy', extra_fields=['category_scores__performance', 'category_scores__accessibility', 'category_scores__best_practices', 'category_scores__seo'])
    
    # Compare analytics
    compare_start1 = request.GET.get("compare_start1")
    compare_end1 = request.GET.get("compare_end1")
    compare_start2 = request.GET.get("compare_start2")
    compare_end2 = request.GET.get("compare_end2")
    
    compare_periods = []
    if compare_start1 and compare_end1:
        compare_periods.append((compare_start1, compare_end1))
    if compare_start2 and compare_end2:
        compare_periods.append((compare_start2, compare_end2))

    compare_data = None
    if len(compare_periods) == 2:
         compare_data = get_compare_data_for_queryset(reports_qs, 'fetch_time', compare_periods, group_by_field='strategy', extra_fields=['category_scores__performance', 'category_scores__accessibility', 'category_scores__best_practices', 'category_scores__seo'])

    return render(
        request,
        "links/psi_reports_list.html",
        {
            "link": link,
            "reports": page_obj_paginated, # Use paginated object
            "mobile_reports": mobile_reports, # Could be page_obj_paginated if paginating mobile
            "desktop_reports": desktop_reports,
            "page_obj": page_obj_paginated, # Standard name for paginator object in template
            "trend_data": trend_data,
            "compare_data": compare_data,
            "compare_start1": compare_start1,
            "compare_end1": compare_end1,
            "compare_start2": compare_start2,
            "compare_end2": compare_end2,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "min_score": min_score_str,
            "max_score": max_score_str,
            "search": search_query, # Use renamed
        },
    )


@login_required
def psi_report_detail(request, report_id):
    report = get_object_or_404(PSIReport.objects.select_related('page', 'field_metrics', 'lab_metrics', 'category_scores').prefetch_related('audits'), id=report_id, user=request.user)
    # field_metrics, lab_metrics, category_scores are now directly accessible via report.field_metrics etc.
    # due to OneToOneField related_name. Audits are accessible via report.audits.all()
    return render(
        request,
        "links/psi_report_detail.html",
        {
            "report": report,
            "field_metrics": getattr(report, "field_metrics", None), # Still good for explicit check
            "lab_metrics": getattr(report, "lab_metrics", None),
            "category_scores": getattr(report, "category_scores", None),
            "audits": report.audits.all(),
        },
    )


@login_required
@require_POST
def bulk_delete_links(request):
    try:
        data = json.loads(request.body)
        ids = data.get("ids", [])
        if not ids:
            return JsonResponse({"status": "error", "message": "No IDs provided."}, status=400)
        Link.objects.filter(id__in=ids, user=request.user).delete()
        return JsonResponse({"status": "success", "message": "Links deleted successfully."})
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
    except Exception as e:
         return JsonResponse({"status": "error", "message": str(e)}, status=500)


def export_psi_reports(request, link_id): # Not login protected, consider if needed
    link = get_object_or_404(Link, id=link_id) # Add user=request.user if login protected
    # This view seems to export PSIReportGroup data, not individual PSIReports.
    # The original code refers to link.psi_reports which doesn't exist directly.
    # Assuming it means to export data related to PSIReportGroups associated with the link's page.
    page = Page.objects.filter(url=link.url, user=link.user).first()
    if not page:
        return JsonResponse([], safe=False)
        
    report_groups = PSIReportGroup.objects.filter(page=page).order_by("-fetch_time")
    data = []
    for group in report_groups:
        mobile = group.reports.filter(strategy='mobile').first()
        desktop = group.reports.filter(strategy='desktop').first()
        data.append({
            "group_id": group.id,
            "fetch_time": group.fetch_time.isoformat(),
            "mobile_report_id": mobile.id if mobile else None,
            "desktop_report_id": desktop.id if desktop else None,
            # Add more fields from reports if needed
        })
    return JsonResponse(data, safe=False)


def export_psi_reports_csv(request, link_id): # Not login protected
    link = get_object_or_404(Link, id=link_id) # Add user=request.user if login protected
    page = Page.objects.filter(url=link.url, user=link.user).first()
    if not page:
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="psi_reports_{link_id}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(["Error"])
        writer.writerow(["No page found for this link to export reports."])
        return response

    reports = PSIReport.objects.filter(page=page).select_related('category_scores').order_by("-fetch_time")
    
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="psi_reports_{link_id}_{page.url.replace("https://", "").replace("http://", "").replace("/", "_")}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(
        ["report_id", "fetch_time", "strategy", "performance_score", "accessibility_score", "best_practices_score", "seo_score", "page_url"]
    )
    for r in reports:
        writer.writerow(
            [
                r.id,
                r.fetch_time.isoformat(),
                r.strategy,
                r.category_scores.performance if r.category_scores else "",
                r.category_scores.accessibility if r.category_scores else "",
                r.category_scores.best_practices if r.category_scores else "",
                r.category_scores.seo if r.category_scores else "",
                page.url,
            ]
        )
    return response


def export_links_csv(request): # Not login protected
    links = Link.objects.filter(user=request.user).order_by("-created_at") # Assuming for logged in user
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="links.csv"'
    writer = csv.writer(response)
    writer.writerow(["id", "title", "url", "description", "created_at", "updated_at"])
    for link_obj in links: # Renamed variable
        writer.writerow(
            [
                link_obj.id,
                link_obj.title,
                link_obj.url,
                link_obj.description,
                link_obj.created_at.isoformat(),
                link_obj.updated_at.isoformat(),
            ]
        )
    return response


@login_required
@require_POST
def delete_psi_report_group(request, group_id):
    group = get_object_or_404(PSIReportGroup, id=group_id, user=request.user)
    group.delete() # This will also delete associated PSIReport instances via CASCADE
    return JsonResponse({"status": "success", "message": "Report group deleted."})


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
@require_POST
def import_links_json(request):
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'status': 'error', 'message': 'No file uploaded.'}, status=400)
        
        file_content = request.FILES['file'].read().decode('utf-8')
        data = json.loads(file_content)
        
        created_count = 0
        existing_count = 0

        for entry in data:
            if 'url' in entry and 'title' in entry:
                link_obj, created = Link.objects.get_or_create( # Renamed variable
                    url=entry['url'],
                    user=request.user, # Ensure uniqueness per user
                    defaults={
                        'title': entry.get('title', ''),
                        'description': entry.get('description', ''),
                    },
                )
                if created:
                    created_count += 1
                else:
                    existing_count +=1
        return JsonResponse({'status': 'success', 'created': created_count, 'existing_skipped': existing_count})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON format in file.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def dashboard(request):
    latest_psi = PSIReport.objects.filter(
        page__url=OuterRef('url'), user=request.user
    ).order_by('-fetch_time')
    latest_ssl = SSLCheck.objects.filter(
        link=OuterRef('pk'), user=request.user # pk refers to Link's primary key
    ).order_by('-checked_at')
    latest_ssl_labs = SSLLabsScan.objects.filter(
        link=OuterRef('pk'), user=request.user
    ).order_by('-scanned_at')

    links_qs = Link.objects.filter(user=request.user).annotate(
        psi_performance_score=Subquery(latest_psi.values('category_scores__performance')[:1], output_field=FloatField()),
        psi_last_checked=Subquery(latest_psi.values('fetch_time')[:1], output_field=DateTimeField()),
        ssl_is_expired=Subquery(latest_ssl.values('is_expired')[:1], output_field=CharField()), # BooleanField or CharField? Model has BooleanField
        ssl_last_checked=Subquery(latest_ssl.values('checked_at')[:1], output_field=DateTimeField()),
        ssl_expiry_date=Subquery(latest_ssl.values('not_after')[:1], output_field=DateTimeField()),
        ssl_warnings_text=Subquery(latest_ssl.values('warnings')[:1], output_field=CharField()),
        ssl_errors_text=Subquery(latest_ssl.values('errors')[:1], output_field=CharField()),
        ssl_labs_grade=Subquery(latest_ssl_labs.values('grade')[:1], output_field=CharField()),
        ssl_labs_scan_status=Subquery(latest_ssl_labs.values('status')[:1], output_field=CharField()),
    )
    
    sites_data = []
    for link_item in links_qs: # Renamed variable
        sites_data.append({
            "link": link_item,
            "psi_status": link_item.psi_performance_score, # Renamed for clarity
            "psi_last_checked": link_item.psi_last_checked,
            "ssl_status": not bool(link_item.ssl_is_expired) if link_item.ssl_is_expired is not None else None, # Convert to boolean
            "ssl_last_checked": link_item.ssl_last_checked,
            "ssl_expiry": link_item.ssl_expiry_date, # Renamed for clarity
            "ssl_warnings": link_item.ssl_warnings_text, # Renamed
            "ssl_errors": link_item.ssl_errors_text, # Renamed
            "ssl_grade": link_item.ssl_labs_grade, # Renamed
            "ssl_labs_status": link_item.ssl_labs_scan_status, # Renamed
            "uptime_status": link_item.uptime_last_status, # Assuming this is 'Up'/'Down' or similar
            "uptime_last_checked": link_item.uptime_last_checked,
            "sec_headers_status": None, # Placeholder
            "sec_headers_last_checked": None, # Placeholder
        })
    return render(request, "links/dashboard.html", {"sites_data": sites_data})


@login_required
def site_detail(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    # Fetch related data efficiently
    page = Page.objects.filter(url=link.url, user=request.user).first()
    psi_reports = PSIReport.objects.none()
    if page:
        psi_reports = PSIReport.objects.filter(page=page, user=request.user).order_by("-fetch_time")
    
    latest_ssl_check = link.ssl_checks.order_by("-checked_at").first()
    latest_ssllabs_scan = link.ssllabs_scans.order_by("-scanned_at").first()
    # Uptime can be fetched from link model's fields or by calling service if live data is needed

    return render(
        request,
        "links/site_detail.html", # Create this template
        {
            "link": link,
            "psi_reports": psi_reports,
            "latest_ssl_check": latest_ssl_check,
            "latest_ssllabs_scan": latest_ssllabs_scan,
            # "uptime_results": uptime_results, # Pass link.uptime_last_status etc.
            # "sec_headers_results": sec_headers_results, # Placeholder
        },
    )


@login_required
@require_POST
def add_site(request):
    try:
        data = json.loads(request.body)
        url = data.get("url")
        title = data.get("title")
        description = data.get("description", "")
        
        if not url or not title:
            return JsonResponse(
                {"status": "error", "message": "Title and URL are required."}, status=400
            )
        # Basic URL validation could be added here if desired
        
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
                    "message": f'Site "{title}" added successfully!'
                }
            )
        else:
            return JsonResponse(
                {"status": "error", "message": "Site with this URL already exists for your account."}, status=400
            )
    except json.JSONDecodeError:
        return JsonResponse({"status":"error", "message": "Invalid JSON."}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required
def profile(request):
    user = request.user # Already settings.AUTH_USER_MODEL
    password_form = PasswordChangeForm(user)
    
    if request.method == "POST":
        if "update_email" in request.POST:
            new_email = request.POST.get("email")
            if new_email and new_email != user.email:
                # Add email validation
                from django.core.validators import validate_email
                from django.core.exceptions import ValidationError
                try:
                    validate_email(new_email)
                    # Check if email is already in use by another user
                    if get_user_model().objects.filter(email=new_email).exclude(pk=user.pk).exists():
                         messages.error(request, "This email address is already in use.")
                    else:
                        user.email = new_email
                        user.save(update_fields=['email'])
                        messages.success(request, "Email updated successfully.")
                except ValidationError:
                    messages.error(request, "Invalid email address.")
            elif new_email == user.email:
                 messages.info(request, "The new email is the same as the current one.")
            else:
                messages.error(request, "Email cannot be empty.")
            return redirect("profile") # Redirect to refresh and show message

        elif "update_password" in request.POST:
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                saved_user = password_form.save() # Renamed variable
                update_session_auth_hash(request, saved_user) # Use saved_user
                messages.success(request, "Password updated successfully.")
                return redirect("profile") # Redirect to refresh and clear form
            else:
                messages.error(request, "Please correct the password errors.")
        
        elif "delete_account" in request.POST:
            # Implement safety: e.g., confirm password or type "DELETE"
            user.delete()
            messages.success(request, "Your account has been deleted.")
            return redirect("account_login") # Or home page
            
    return render(
        request,
        "links/profile.html",
        {
            "password_form": password_form,
            # "email_updated" & "password_updated" flags are not very useful with redirects
        },
    )


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("account_login")


@login_required
def features_page(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    features = [
        {
            "name": "PageSpeed Insights",
            "key": "psi",
            "description": "Analyze site performance using Google PSI.",
            "has_history": True,
            "run_url": reverse('fetch_psi_report', args=[link.id]), # Use reverse
            "history_url": reverse('psi_reports_list', args=[link.id]), # Use reverse
        },
        {
            "name": "Uptime Monitoring",
            "key": "uptime",
            "description": "Check site uptime status using UptimeRobot.",
            "has_history": True, # Uptime history is available
            "run_url": reverse('uptime_feature_run', args=[link.id]),
            "history_url": reverse('uptime_history', args=[link.id]),
        },
        {
            "name": "SSL Certificate Check", # Renamed for clarity
            "key": "ssl",
            "description": "Check SSL certificate validity, expiry, and configuration.",
            "has_history": True,
            "run_url": reverse('ssl_feature_run', args=[link.id]),
            "history_url": reverse('ssl_history', args=[link.id]),
        },
        {
            "name": "SSL Labs Advanced Scan",
            "key": "ssllabs",
            "description": "Run a deep SSL security scan and get a grade (A+ to F) and vulnerabilities.",
            "has_history": True,
            "run_url": reverse('ssl_labs_feature_run', args=[link.id]),
            "history_url": reverse('ssl_labs_history', args=[link.id]),
        },
    ]
    return render(
        request, "links/features_page.html", {"link": link, "features": features}
    )


@login_required
def uptime_feature_run(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    context = {"link": link, "monitor": None, "error": None}
    try:
        monitor = UptimeRobotService.get_monitor_details(link, request.user) # Using get_monitor_details
        
        custom_uptime_ratio_str = monitor.get("custom_uptime_ratio", "")
        uptime_ratios = [r.strip() for r in custom_uptime_ratio_str.split("-")] if custom_uptime_ratio_str else []
        
        last_response_time = None
        if monitor.get("response_times"):
            last_response_time = monitor["response_times"][-1].get("value")
        if not last_response_time: # Fallback if last response time is 0 or not present
             last_response_time = monitor.get("average_response_time")


        context.update({
            "monitor": monitor,
            "uptime_ratios": uptime_ratios,
            "last_response_time": last_response_time,
            "alert_contacts": monitor.get("alert_contacts", []),
            "maintenance_windows": monitor.get("maintenance_windows", []),
            "ssl_info": monitor.get("ssl"), # Renamed from "ssl" to avoid conflict
            "tags_list": [t.strip() for t in monitor.get("tags","").split(',')] if monitor.get("tags") else [], # Assuming tags are comma-separated
            "raw_json": json.dumps(monitor, indent=2),
        })
    except Exception as e:
        context["error"] = str(e)
    return render(request, "links/uptime_feature_run.html", context)


@login_required
def uptime_history(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    context = {"link": link, "logs": [], "error": None}
    try:
        monitor_data = UptimeRobotService.get_monitor_details(link, request.user) # Fetch fresh data
        logs = monitor_data.get("logs", [])
        
        log_type_filter = request.GET.get("type")
        if log_type_filter:
            logs = [log for log in logs if str(log.get("type")) == log_type_filter]
        
        sort_param = request.GET.get("sort", "-datetime") # Default sort
        reverse_sort = sort_param.startswith("-")
        sort_key_name = sort_param.lstrip("-")
        
        # Ensure logs have the sort key or provide a default for sorting
        logs = sorted(logs, key=lambda x: x.get(sort_key_name, 0 if 'time' in sort_key_name else ''), reverse=reverse_sort)

        page_num = int(request.GET.get("page", 1))
        per_page_count = int(request.GET.get("per_page", 20))
        
        paginator_logs = Paginator(logs, per_page_count)
        try:
            logs_page_obj = paginator_logs.page(page_num)
        except PageNotAnInteger:
            logs_page_obj = paginator_logs.page(1)
        except EmptyPage:
            logs_page_obj = paginator_logs.page(paginator_logs.num_pages)

        trend_data = get_trend_data_for_logs(logs, 'datetime') # Pass all logs for trend
        
        compare_start1 = request.GET.get("compare_start1")
        compare_end1 = request.GET.get("compare_end1")
        compare_start2 = request.GET.get("compare_start2")
        compare_end2 = request.GET.get("compare_end2")
        
        compare_log_periods = []
        if compare_start1 and compare_end1:
            compare_log_periods.append((compare_start1, compare_end1))
        if compare_start2 and compare_end2:
            compare_log_periods.append((compare_start2, compare_end2))
        
        compare_log_data = None
        if len(compare_log_periods) == 2:
            compare_log_data = get_compare_data_for_logs(logs, 'datetime', compare_log_periods) # Pass all logs for compare

        context.update({
            "logs": logs_page_obj, # Paginated logs
            "total": paginator_logs.count,
            "page": page_num,
            "per_page": per_page_count,
            "log_type": log_type_filter,
            "sort": sort_param,
            "trend_data": trend_data,
            "compare_data": compare_log_data,
            "compare_start1": compare_start1,
            "compare_end1": compare_end1,
            "compare_start2": compare_start2,
            "compare_end2": compare_end2,
        })
    except Exception as e:
        context["error"] = str(e)
    return render(request, "links/uptime_history.html", context)


@login_required
def export_uptime_logs_csv(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    try:
        monitor = UptimeRobotService.get_monitor_details(link, request.user)
        logs = monitor.get("logs", [])
        
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="uptime_logs_{link.url.replace("https://", "").replace("http://", "").replace("/", "_")}_{link_id}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(["datetime", "type (1=Down, 2=Up, 99=Paused)", "reason_detail", "duration_seconds", "status_code"])
        for log in logs:
            writer.writerow(
                [
                    datetime.fromtimestamp(log.get("datetime")).isoformat() if log.get("datetime") else "",
                    log.get("type"),
                    log.get("reason", {}).get("detail", ""),
                    log.get("duration", ""),
                    log.get("status_code", "") 
                ]
            )
        return response
    except Exception as e:
        # Handle error, maybe return a CSV with error message
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="error_export_uptime_logs_{link_id}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(["Error exporting logs:", str(e)])
        return response


@login_required
def export_uptime_logs_json(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    try:
        monitor = UptimeRobotService.get_monitor_details(link, request.user)
        logs = monitor.get("logs", [])
        return JsonResponse(logs, safe=False, json_dumps_params={'indent': 2})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def settings_view(request):
    SERVICES = [
        {"key": "psi", "name": "Google PageSpeed Insights", "help_url": "https://developers.google.com/speed/docs/insights/v5/get-started", "instructions": "Create a project in Google Cloud, enable the PageSpeed Insights API, and generate an API key.", "limitations": "Free tier: 25,000 requests/day. Quotas may change."},
        {"key": "uptimerobot", "name": "UptimeRobot", "help_url": "https://uptimerobot.com/dashboard#mySettings", "instructions": "Log in to UptimeRobot, go to My Settings, and copy your Main API Key.", "limitations": "Free tier: 50 monitors, 5-minute checks. Quotas may change."},
    ]
    user = request.user
    form_valid_status = None # Renamed

    if request.method == "POST":
        form = APIKeyForm(request.POST, user=user)
        if form.is_valid():
            for service_config in SERVICES: # Renamed variable
                field_name = f"key_{service_config['key']}"
                value = form.cleaned_data.get(field_name, "").strip()
                
                if value: # If key is provided
                    key_obj, created = UserAPIKey.objects.update_or_create( # Use update_or_create
                        user=user, 
                        service=service_config["key"],
                        defaults={'key': value, 'status': 'set'}
                    )
                    messages.success(request, f"API key for {service_config['name']} {'saved' if created else 'updated'}.")
                else: # If key is empty, remove existing if any
                    deleted_count, _ = UserAPIKey.objects.filter(user=user, service=service_config["key"]).delete()
                    if deleted_count > 0:
                        messages.info(request, f"API key for {service_config['name']} removed.")
            
            form_valid_status = True
            messages.success(request, "Settings saved successfully.") # General success message
            return redirect('settings') # Redirect to show messages and clear POST
        else:
            form_valid_status = False
            messages.error(request, "Please correct the errors below.")
    else:
        form = APIKeyForm(user=user) # Pre-populate with existing keys

    # Prepare keys for template display
    current_keys = {k.service: k for k in UserAPIKey.objects.filter(user=user)}
    for service_config in SERVICES: # Use same var name as above
        k = current_keys.get(service_config["key"])
        if k:
            service_config['status'] = "set" if k.key and k.key != "DUMMY_KEY_CHANGE_ME" else "Not set"
            service_config['actual_key_value_for_template_debug_only'] = k.key # For DUMMY_KEY check in template
        else:
            service_config['status'] = "Not set"
            service_config['actual_key_value_for_template_debug_only'] = None


    return render(
        request,
        "links/settings.html",
        {
            "services": SERVICES, # Pass modified services list
            "keys": current_keys, # Still useful for direct access if needed
            "form": form,
            "form_valid": form_valid_status, # Use renamed
        },
    )


@login_required
def ssl_labs_feature_run(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    error_message = None # Renamed
    scan_result = None # Renamed

    if request.method == "POST":
        try:
            scan_result = SSLLabsService.run_scan(link, request.user)
            if scan_result: # run_scan returns a list or a single object
                 messages.success(request, f"SSL Labs scan for {link.title} completed.")
            else:
                 messages.warning(request, f"SSL Labs scan for {link.title} did not return results immediately. Check history.")
        except Exception as e:
            error_message = str(e)
            messages.error(request, f"SSL Labs scan failed: {error_message}")
        return redirect('ssl_labs_feature_run', link_id=link.id) # Redirect to show messages

    latest_scan = link.ssllabs_scans.order_by("-scanned_at").first()
    
    return render(
        request,
        "links/ssl_labs_feature_run.html",
        {
            "link": link,
            "scan": scan_result or latest_scan, # Show new scan if available, else latest
            "error": error_message, # This will be None on GET after redirect
        },
    )


@login_required
def ssl_history(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    checks_qs = link.ssl_checks.order_by("-checked_at") # Renamed variable
    
    trend_start_date = request.GET.get("trend_start")
    trend_end_date = request.GET.get("trend_end")
    trend_data_result = None # Renamed
    if trend_start_date and trend_end_date:
        trend_data_result = get_trend_data_for_queryset(checks_qs, 'checked_at', group_by_field=None, extra_fields=['not_after'])
    
    compare_start1 = request.GET.get("compare_start1")
    compare_end1 = request.GET.get("compare_end1")
    compare_start2 = request.GET.get("compare_start2")
    compare_end2 = request.GET.get("compare_end2")
    
    compare_data_result = None # Renamed
    compare_ssl_periods = []
    if compare_start1 and compare_end1:
        compare_ssl_periods.append((compare_start1, compare_end1))
    if compare_start2 and compare_end2:
        compare_ssl_periods.append((compare_start2, compare_end2))

    if len(compare_ssl_periods) == 2:
        compare_data_result = get_compare_data_for_queryset(checks_qs, 'checked_at', compare_ssl_periods, group_by_field=None, extra_fields=['not_after'])
        
    return render(
        request,
        "links/ssl_history.html",
        {
            "link": link,
            "checks": checks_qs,
            "trend_data": trend_data_result,
            "trend_start": trend_start_date, # Pass back to prefill form
            "trend_end": trend_end_date,     # Pass back to prefill form
            "compare_data": compare_data_result,
            "compare_start1": compare_start1,
            "compare_end1": compare_end1,
            "compare_start2": compare_start2,
            "compare_end2": compare_end2,
        },
    )


@login_required
def ssl_labs_history(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    scans_qs = link.ssllabs_scans.order_by("-scanned_at") # Renamed
    
    trend_start_date_labs = request.GET.get("trend_start") # Suffix to avoid conflict if sharing template
    trend_end_date_labs = request.GET.get("trend_end")
    trend_data_labs = None
    if trend_start_date_labs and trend_end_date_labs:
        trend_data_labs = get_trend_data_for_queryset(scans_qs, 'scanned_at', group_by_field='grade', extra_fields=['status'])

    compare_start1_labs = request.GET.get("compare_start1")
    compare_end1_labs = request.GET.get("compare_end1")
    compare_start2_labs = request.GET.get("compare_start2")
    compare_end2_labs = request.GET.get("compare_end2")
    
    compare_data_labs = None
    compare_ssllabs_periods = []
    if compare_start1_labs and compare_end1_labs:
        compare_ssllabs_periods.append((compare_start1_labs, compare_end1_labs))
    if compare_start2_labs and compare_end2_labs:
        compare_ssllabs_periods.append((compare_start2_labs, compare_end2_labs))

    if len(compare_ssllabs_periods) == 2:
        compare_data_labs = get_compare_data_for_queryset(scans_qs, 'scanned_at', compare_ssllabs_periods, group_by_field='grade', extra_fields=['status'])
        
    return render(
        request,
        "links/ssl_labs_history.html",
        {
            "link": link,
            "scans": scans_qs,
            "trend_data": trend_data_labs,
            "trend_start": trend_start_date_labs,
            "trend_end": trend_end_date_labs,
            "compare_data": compare_data_labs,
            "compare_start1": compare_start1_labs,
            "compare_end1": compare_end1_labs,
            "compare_start2": compare_start2_labs,
            "compare_end2": compare_end2_labs,
        },
    )


@login_required
def ssl_feature_run(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    error_message_ssl = None # Renamed
    ssl_check_result = None # Renamed

    if request.method == "POST":
        try:
            ssl_check_result = SSLService.check_certificate(link, request.user)
            if ssl_check_result:
                 messages.success(request, f"SSL check for {link.title} completed.")
            else:
                 messages.warning(request, f"SSL check for {link.title} did not return results.")
        except Exception as e:
            error_message_ssl = str(e)
            messages.error(request, f"SSL check failed: {error_message_ssl}")
        return redirect('ssl_feature_run', link_id=link.id) # Redirect to show messages

    latest_check = link.ssl_checks.order_by("-checked_at").first()
    return render(
        request,
        "links/ssl_feature_run.html",
        {
            "link": link,
            "ssl_check": ssl_check_result or latest_check, # Show new if available, else latest
            "error": error_message_ssl, # Will be None on GET after redirect
        },
    )


@login_required
@require_GET # Explicitly state this is a GET view
def dashboard_table(request):
    # This view is intended to return only the HTML for the table body.
    # The logic should be identical to the dashboard view for fetching sites_data.
    latest_psi = PSIReport.objects.filter(
        page__url=OuterRef('url'), user=request.user
    ).order_by('-fetch_time')
    latest_ssl = SSLCheck.objects.filter(
        link=OuterRef('pk'), user=request.user
    ).order_by('-checked_at')
    latest_ssl_labs = SSLLabsScan.objects.filter(
        link=OuterRef('pk'), user=request.user
    ).order_by('-scanned_at')

    links_qs = Link.objects.filter(user=request.user).annotate(
        psi_performance_score=Subquery(latest_psi.values('category_scores__performance')[:1], output_field=FloatField()),
        psi_last_checked=Subquery(latest_psi.values('fetch_time')[:1], output_field=DateTimeField()),
        ssl_is_expired=Subquery(latest_ssl.values('is_expired')[:1], output_field=CharField()),
        ssl_last_checked=Subquery(latest_ssl.values('checked_at')[:1], output_field=DateTimeField()),
        ssl_expiry_date=Subquery(latest_ssl.values('not_after')[:1], output_field=DateTimeField()),
        ssl_warnings_text=Subquery(latest_ssl.values('warnings')[:1], output_field=CharField()),
        ssl_errors_text=Subquery(latest_ssl.values('errors')[:1], output_field=CharField()),
        ssl_labs_grade=Subquery(latest_ssl_labs.values('grade')[:1], output_field=CharField()),
        ssl_labs_scan_status=Subquery(latest_ssl_labs.values('status')[:1], output_field=CharField()),
    )
    
    sites_data = []
    for link_item in links_qs:
        sites_data.append({
            "link": link_item,
            "psi_status": link_item.psi_performance_score,
            "psi_last_checked": link_item.psi_last_checked,
            "ssl_status": not bool(link_item.ssl_is_expired) if link_item.ssl_is_expired is not None else None,
            "ssl_last_checked": link_item.ssl_last_checked,
            "ssl_expiry": link_item.ssl_expiry_date,
            "ssl_warnings": link_item.ssl_warnings_text,
            "ssl_errors": link_item.ssl_errors_text,
            "ssl_grade": link_item.ssl_labs_grade,
            "ssl_labs_status": link_item.ssl_labs_scan_status,
            "uptime_status": link_item.uptime_last_status,
            "uptime_last_checked": link_item.uptime_last_checked,
            "sec_headers_status": None, 
            "sec_headers_last_checked": None,
        })
        
    html = render_to_string('links/dashboard_table_body.html', {'sites_data': sites_data}, request=request)
    return HttpResponse(html)