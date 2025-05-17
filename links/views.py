from django.shortcuts import render
from .models import Link

def home(request):
    # Simple intro page
    return render(request, 'home.html')

def sites(request):
    # Fetch all stored links and pass them to the template
    links = Link.objects.all()
    return render(request, 'sites.html', {'links': links})
