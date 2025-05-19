from django.shortcuts import render, get_object_or_404
from django_filters import FilterSet, CharFilter
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from .models import Link, PSIReport
from .services import PSIService
import json
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import csv


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
        mobile_report, desktop_report = PSIService.fetch_both_reports(link.url)
        psi_report = PSIReport.objects.create(
            link=link,
            mobile_report=mobile_report,
            desktop_report=desktop_report
        )
        return JsonResponse({
            'status': 'success',
            'message': 'PSI report fetched successfully',
            'report_id': psi_report.id
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@require_POST
@csrf_exempt
def delete_psi_report(request, report_id):
    try:
        report = get_object_or_404(PSIReport, id=report_id)
        report.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def psi_reports_list(request, link_id):
    link = get_object_or_404(Link, id=link_id)
    reports = link.psi_reports.all()
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
        'page_obj': page_obj
    })


def psi_report_detail(request, report_id):
    report = get_object_or_404(PSIReport, id=report_id)
    # Defensive: get the nested data or None if missing
    def get_lhr(report_json):
        if report_json and isinstance(report_json, dict):
            return report_json.get('lighthouseResult')
        return None
    mobile_lhr = get_lhr(report.mobile_report)
    desktop_lhr = get_lhr(report.desktop_report)
    return render(request, 'links/psi_report_detail.html', {
        'report': report,
        'mobile_lhr': mobile_lhr,
        'desktop_lhr': desktop_lhr,
    })


@require_POST
@csrf_exempt
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