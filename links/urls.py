from django.urls import path

from . import views

urlpatterns = [
    path("", views.root_redirect, name="root_redirect"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("sites/", views.link_list, name="link_list"),
    path(
        "sites/<int:link_id>/fetch-psi/",
        views.fetch_psi_report,
        name="fetch_psi_report",
    ),
    path(
        "sites/<int:link_id>/reports/", views.psi_reports_list, name="psi_reports_list"
    ),
    path("reports/<int:report_id>/", views.psi_report_detail, name="psi_report_detail"),
    path(
        "reports/<int:report_id>/delete/",
        views.delete_psi_report,
        name="delete_psi_report",
    ),
    path("sites/bulk-delete/", views.bulk_delete_links, name="bulk_delete_links"),
    path(
        "sites/<int:link_id>/reports/export/csv/",
        views.export_psi_reports_csv,
        name="export_psi_reports_csv",
    ),
    path("sites/export/csv/", views.export_links_csv, name="export_links_csv"),
    path(
        "reports/group/<int:group_id>/delete/",
        views.delete_psi_report_group,
        name="delete_psi_report_group",
    ),
    path("sites/export/json/", views.export_links_json, name="export_links_json"),
    path("sites/import/json/", views.import_links_json, name="import_links_json"),
    path("sites/<int:link_id>/", views.site_detail, name="site_detail"),
    path("sites/add/", views.add_site, name="add_site"),
    path("profile/", views.profile, name="profile"),
]
