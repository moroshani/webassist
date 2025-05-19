from django.shortcuts import render
from django_filters import FilterSet, CharFilter
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Link

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