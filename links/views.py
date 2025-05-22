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

from .models import Link, Page, PSIReport, PSIReportGroup
from .services import PSIService


class LinkFilter(FilterSet):
    title = CharFilter(lookup_expr='icontains')
    description = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Link
        fields = ['title', 'description']


def home(request):
    return render(request, 'links/home.html')


@login_required
def link_list(request):
    links = Link.objects.filter(user=request.user)
    link_filter = LinkFilter(request.GET, queryset=links)
    paginator = Paginator(link_filter.qs, 10)  # 10 links per page
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('links/partials/link_table.html', {
            'links': page_obj
        }, request=request)
        return JsonResponse({'html': html})

    return render(request, 'links/link_list.html', {
        'filter': link_filter,
        'links': page_obj,
        'page_obj': page_obj
    })


@login_required
@require_POST
def fetch_psi_report(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    try:
        group, mobile_report, desktop_report = PSIService.fetch_and_store_report_group(link.url, user=request.user)
        return JsonResponse({
            'status': 'success',
            'message': 'PSI reports fetched and stored successfully',
            'group_id': group.id,
            'mobile_report_id': mobile_report.id,
            'desktop_report_id': desktop_report.id
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def delete_psi_report(request, report_id):
    report = get_object_or_404(PSIReport, id=report_id, user=request.user)
    report.delete()
    return JsonResponse({'status': 'success'})


@login_required
def psi_reports_list(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    page = Page.objects.filter(url=link.url, user=request.user).first()
    reports = page.psi_reports.filter(user=request.user) if page else PSIReport.objects.none()
    mobile_reports = reports.filter(strategy='mobile')
    desktop_reports = reports.filter(strategy='desktop')
    paginator = Paginator(reports, 10)  # 10 reports per page
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return render(request, 'links/psi_reports_list.html', {
        'link': link,
        'reports': page_obj,
        'mobile_reports': mobile_reports,
        'desktop_reports': desktop_reports,
        'page_obj': page_obj
    })


@login_required
def psi_report_detail(request, report_id):
    report = get_object_or_404(PSIReport, id=report_id, user=request.user)
    field_metrics = getattr(report, 'field_metrics', None)
    lab_metrics = getattr(report, 'lab_metrics', None)
    category_scores = getattr(report, 'category_scores', None)
    audits = report.audits.all()
    return render(request, 'links/psi_report_detail.html', {
        'report': report,
        'field_metrics': field_metrics,
        'lab_metrics': lab_metrics,
        'category_scores': category_scores,
        'audits': audits,
    })


@login_required
@require_POST
def bulk_delete_links(request):
    data = json.loads(request.body)
    ids = data.get('ids', [])
    Link.objects.filter(id__in=ids, user=request.user).delete()
    return JsonResponse({'status': 'success'})


def export_psi_reports(request, link_id):
    link = get_object_or_404(Link, id=link_id)
    reports = link.psi_reports.all().order_by('-created_at')
    data = [
        {
            'id': r.id,
            'created_at': r.created_at.isoformat(),
            'mobile_report': r.mobile_report,
            'desktop_report': r.desktop_report,
        }
        for r in reports
    ]
    return JsonResponse(data, safe=False)


def export_psi_reports_csv(request, link_id):
    link = get_object_or_404(Link, id=link_id)
    reports = link.psi_reports.all().order_by('-created_at')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="psi_reports_{link_id}.csv"'
    writer = csv.writer(response)
    writer.writerow(['id', 'created_at', 'mobile_performance', 'desktop_performance', 'link_id'])
    for r in reports:
        def get_score(report):
            try:
                return report['lighthouseResult']['categories']['performance']['score']
            except Exception:
                return ''
        writer.writerow([
            r.id,
            r.created_at.isoformat(),
            get_score(r.mobile_report),
            get_score(r.desktop_report),
            link.id
        ])
    return response


def export_links_csv(request):
    links = Link.objects.all().order_by('-created_at')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="links.csv"'
    writer = csv.writer(response)
    writer.writerow(['id', 'title', 'url', 'description', 'created_at', 'updated_at'])
    for link in links:
        writer.writerow([
            link.id,
            link.title,
            link.url,
            link.description,
            link.created_at.isoformat(),
            link.updated_at.isoformat()
        ])
    return response


@login_required
@require_POST
def delete_psi_report_group(request, group_id):
    group = get_object_or_404(PSIReportGroup, id=group_id, user=request.user)
    group.delete()
    return JsonResponse({'status': 'success'})


@login_required
def export_links_json(request):
    links = Link.objects.filter(user=request.user).order_by('-created_at')
    data = [
        {
            'id': link.id,
            'title': link.title,
            'url': link.url,
            'description': link.description,
            'created_at': link.created_at.isoformat(),
            'updated_at': link.updated_at.isoformat(),
        }
        for link in links
    ]
    return JsonResponse(data, safe=False)


@login_required
@csrf_exempt
@require_POST
def import_links_json(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = json.loads(request.FILES['file'].read().decode())
        created = 0
        for entry in data:
            if 'url' in entry and 'title' in entry:
                Link.objects.get_or_create(
                    url=entry['url'],
                    defaults={
                        'title': entry.get('title', ''),
                        'description': entry.get('description', ''),
                        'user': request.user,
                    }
                )
                created += 1
        return JsonResponse({'status': 'success', 'created': created})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def dashboard(request):
    links = Link.objects.filter(user=request.user)
    sites_data = []
    for link in links:
        last_psi = PSIReport.objects.filter(page__url=link.url, user=request.user).order_by('-fetch_time').first()
        # Placeholder values for future features
        ssl_status = None
        ssl_last_checked = None
        uptime_status = None
        uptime_last_checked = None
        sec_headers_status = None
        sec_headers_last_checked = None
        sites_data.append({
            'link': link,
            'psi_status': last_psi.raw_json['lighthouseResult']['categories']['performance']['score'] if last_psi and last_psi.raw_json else None,
            'psi_last_checked': last_psi.fetch_time if last_psi else None,
            'ssl_status': ssl_status,
            'ssl_last_checked': ssl_last_checked,
            'uptime_status': uptime_status,
            'uptime_last_checked': uptime_last_checked,
            'sec_headers_status': sec_headers_status,
            'sec_headers_last_checked': sec_headers_last_checked,
        })
    return render(request, 'links/dashboard.html', {'sites_data': sites_data})


@login_required
def site_detail(request, link_id):
    link = get_object_or_404(Link, id=link_id, user=request.user)
    psi_reports = PSIReport.objects.filter(page__url=link.url, user=request.user).order_by('-fetch_time')
    # Placeholders for future features
    ssl_results = None
    uptime_results = None
    sec_headers_results = None
    return render(request, 'links/site_detail.html', {
        'link': link,
        'psi_reports': psi_reports,
        'ssl_results': ssl_results,
        'uptime_results': uptime_results,
        'sec_headers_results': sec_headers_results,
    })


@login_required
@require_POST
def add_site(request):
    data = json.loads(request.body)
    url = data.get('url')
    title = data.get('title')
    description = data.get('description', '')
    if not url or not title:
        return JsonResponse({'status': 'error', 'message': 'Title and URL are required.'}, status=400)
    link, created = Link.objects.get_or_create(url=url, user=request.user, defaults={'title': title, 'description': description})
    if created:
        messages.success(request, f'Site "{title}" added successfully!')
        return JsonResponse({'status': 'success', 'link_id': link.id, 'title': link.title, 'url': link.url})
    else:
        return JsonResponse({'status': 'error', 'message': 'Site already exists.'}, status=400)


@login_required
def profile(request):
    user = request.user
    password_form = PasswordChangeForm(user)
    email_updated = False
    password_updated = False
    if request.method == 'POST':
        if 'update_email' in request.POST:
            new_email = request.POST.get('email')
            if new_email and new_email != user.email:
                user.email = new_email
                user.save()
                email_updated = True
                messages.success(request, 'Email updated successfully.')
        elif 'update_password' in request.POST:
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                password_updated = True
                messages.success(request, 'Password updated successfully.')
        elif 'delete_account' in request.POST:
            user.delete()
            messages.success(request, 'Your account has been deleted.')
            return redirect('home')
    return render(request, 'links/profile.html', {
        'user': user,
        'password_form': password_form,
        'email_updated': email_updated,
        'password_updated': password_updated,
    })


def root_redirect(request):
    return redirect('dashboard') 