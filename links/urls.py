from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('sites/', views.link_list, name='link_list'),
    path('sites/<int:link_id>/fetch-psi/', views.fetch_psi_report, name='fetch_psi_report'),
    path('sites/<int:link_id>/reports/', views.psi_reports_list, name='psi_reports_list'),
    path('reports/<int:report_id>/', views.psi_report_detail, name='psi_report_detail'),
] 