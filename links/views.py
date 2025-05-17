from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Link

def home(request):
    return render(request, 'home.html')

def sites(request):
    queryset = Link.objects.all()

    # --- Search ---
    query = request.GET.get('q', '').strip()
    if query:
        queryset = queryset.filter(url__icontains=query)

    # --- Sorting ---
    sort = request.GET.get('sort')
    if sort in ('url', '-url'):
        queryset = queryset.order_by(sort)

    # --- Pagination (10 per page) ---
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'sites.html', {
        'page_obj': page_obj,
        'query': query,
        'sort': sort,
    })
