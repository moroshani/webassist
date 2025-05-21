from django.shortcuts import render, get_object_or_404
from django_filters import FilterSet, CharFilter
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST, require_GET
from .models import Link, Page, PSIReport, PSIReportGroup
from .services import PSIService
import json
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import csv
import io


class LinkFilter(FilterSet):
    title = CharFilter(lookup_expr='icontains')
    description = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Link
        fields = ['title', 'description']


def home(request):
    return render(request, 'links/home.html')


def link_list(request):
    links = Link.objects.all()
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


@require_POST
def fetch_psi_report(request, link_id):
    link = get_object_or_404(Link, id=link_id)
    try:
        group, mobile_report, desktop_report = PSIService.fetch_and_store_report_group(link.url)
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


@require_POST
def delete_psi_report(request, report_id):
    try:
        report = get_object_or_404(PSIReport, id=report_id)
        report.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def psi_reports_list(request, link_id):
    link = get_object_or_404(Link, id=link_id)
    page = Page.objects.filter(url=link.url).first()
    reports = page.psi_reports.all() if page else PSIReport.objects.none()
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


def psi_report_detail(request, report_id):
    report = get_object_or_404(PSIReport, id=report_id)
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


@require_POST
def bulk_delete_links(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        Link.objects.filter(id__in=ids).delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


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


@require_POST
def delete_psi_report_group(request, group_id):
    try:
        group = get_object_or_404(PSIReportGroup, id=group_id)
        group.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_GET
def export_links_json(request):
    links = Link.objects.all().order_by('-created_at')
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
                    }
                )
                created += 1
        return JsonResponse({'status': 'success', 'created': created})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400) 