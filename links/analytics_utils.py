from datetime import datetime, timedelta
from django.db.models import Avg, Min, Max

def get_trend_data_for_queryset(qs, date_field, group_by_field=None, extra_fields=None):
    """
    Returns trend analytics for a queryset over a date range.
    qs: QuerySet
    date_field: str, the field name for date filtering
    group_by_field: str, optional, to group by a field (e.g., 'strategy')
    extra_fields: list of str, extra fields to include in points
    """
    def get_stats(qs):
        return {
            "avg": qs.aggregate(
                **{f: Avg(f) for f in extra_fields or []}
            ),
            "min": qs.aggregate(
                **{f: Min(f) for f in extra_fields or []}
            ),
            "max": qs.aggregate(
                **{f: Max(f) for f in extra_fields or []}
            ),
            "points": [
                {f: getattr(r, f, None) for f in (extra_fields or []) | {date_field}}
                for r in qs.order_by(date_field)
            ],
        }
    if group_by_field:
        groups = qs.values_list(group_by_field, flat=True).distinct()
        return {g: get_stats(qs.filter(**{group_by_field: g})) for g in groups}
    else:
        return get_stats(qs)

def get_compare_data_for_queryset(qs, date_field, periods, group_by_field=None, extra_fields=None):
    """
    Returns compare analytics for a queryset over two periods.
    periods: list of (start, end) tuples (as date strings)
    """
    def filter_period(qs, start, end):
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
        return qs.filter(**{f"{date_field}__gte": start_dt, f"{date_field}__lt": end_dt})
    return {
        f"period{i+1}": get_trend_data_for_queryset(filter_period(qs, *period), date_field, group_by_field, extra_fields)
        for i, period in enumerate(periods)
    }

def get_trend_data_for_logs(logs, date_field):
    """
    Returns trend analytics for a list of dict logs (e.g., uptime logs).
    """
    # Example for Uptime logs
    up_count = sum(1 for log in logs if log.get("type") == 2)
    down_count = sum(1 for log in logs if log.get("type") == 1)
    total_checks = len(logs)
    uptime_percent = (up_count / total_checks * 100) if total_checks else 0
    longest = 0
    current = 0
    for log in logs:
        if log.get("type") == 1:
            current += 1
            if current > longest:
                longest = current
        else:
            current = 0
    response_times = [
        rt.get("value")
        for log in logs
        for rt in log.get("response_times", [])
        if rt.get("value") is not None
    ]
    min_response = min(response_times) if response_times else None
    max_response = max(response_times) if response_times else None
    avg_response = sum(response_times) / len(response_times) if response_times else None
    points = [
        {"date": log[date_field][:16], "status": log.get("type")}
        for log in logs
    ]
    return {
        "uptime_percent": uptime_percent,
        "downtime_events": down_count,
        "longest_downtime": longest,
        "total_checks": total_checks,
        "points": points,
        "logs": logs,
        "min_response": min_response,
        "max_response": max_response,
        "avg_response": avg_response,
    }

def get_compare_data_for_logs(logs, date_field, periods):
    """
    Returns compare analytics for logs over two periods.
    periods: list of (start, end) tuples (as date strings)
    """
    def filter_period(logs, start, end):
        return [log for log in logs if log.get(date_field) and start <= log[date_field][:10] <= end]
    return {
        f"period{i+1}": get_trend_data_for_logs(filter_period(logs, *period), date_field)
        for i, period in enumerate(periods)
    } 