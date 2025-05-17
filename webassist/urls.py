from django.contrib import admin
from django.urls import path
from links import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Home page
    path('', views.home, name='home'),
    # Sites listing page
    path('sites/', views.sites, name='sites'),
]
