from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('sites/', views.link_list, name='link_list'),
] 