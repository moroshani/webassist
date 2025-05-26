from django.urls import path

from . import views

urlpatterns = [
    path("", views.root_redirect, name="root_redirect"),
    path("dashboard/", views.dashboard, name="dashboard"),
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
    path("sites/<int:link_id>/features/", views.features_page, name="features_page"),
    path("sites/<int:link_id>/features/uptime/", views.uptime_feature_run, name="uptime_feature_run"),
    path("sites/<int:link_id>/features/uptime/history/", views.uptime_history, name="uptime_history"),
    path("sites/<int:link_id>/features/uptime/history/export/csv/", views.export_uptime_logs_csv, name="export_uptime_logs_csv"),
    path("sites/<int:link_id>/features/uptime/history/export/json/", views.export_uptime_logs_json, name="export_uptime_logs_json"),
    path("sites/<int:link_id>/features/ssl/", views.ssl_feature_run, name="ssl_feature_run"),
    path("sites/<int:link_id>/features/ssl-labs/", views.ssl_labs_feature_run, name="ssl_labs_feature_run"),
    path("sites/<int:link_id>/features/ssl/history/", views.ssl_history, name="ssl_history"),
    path("sites/<int:link_id>/features/ssl-labs/history/", views.ssl_labs_history, name="ssl_labs_history"),
    path("settings/", views.settings_view, name="settings"),
]
