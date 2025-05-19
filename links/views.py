from django.shortcuts import render
from django_filters import FilterSet, CharFilter
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
    return render(request, 'links/link_list.html', {
        'filter': link_filter,
        'links': link_filter.qs
    }) 