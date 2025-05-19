from django.shortcuts import render, get_object_or_404
from django_filters import FilterSet, CharFilter
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from .models import Link, PSIReport
from .services import PSIService

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
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('links/partials/link_table.html', {
            'links': link_filter.qs
        }, request=request)
        return JsonResponse({'html': html})
    
    return render(request, 'links/link_list.html', {
        'filter': link_filter,
        'links': link_filter.qs
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

def psi_reports_list(request, link_id):
    link = get_object_or_404(Link, id=link_id)
    reports = link.psi_reports.all()
    return render(request, 'links/psi_reports_list.html', {
        'link': link,
        'reports': reports
    })

def psi_report_detail(request, report_id):
    report = get_object_or_404(PSIReport, id=report_id)
    return render(request, 'links/psi_report_detail.html', {
        'report': report
    }) 