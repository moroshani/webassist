from django import template

register = template.Library()


@register.filter
def getitem(obj, key):
    if obj is None:
        return None
    # For dict-like objects
    if hasattr(obj, "get"):
        return obj.get(key, None)
    # For Django forms (support bracket access)
    try:
        return obj[key]
    except (KeyError, TypeError, AttributeError):
        return None


@register.filter
def split(value, delimiter):
    return value.split(delimiter)


@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ""
