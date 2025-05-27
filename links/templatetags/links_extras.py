from django import template

register = template.Library()


@register.filter
def getitem(obj, key):
    if obj is None:
        return None
    # For Django forms and dict-like objects
    try:
        return obj[key]
    except (KeyError, TypeError, AttributeError):
        # Fallback for objects that might have a .get method (though less common for forms directly)
        if hasattr(obj, "get"):
            return obj.get(key)
        return None


@register.filter
def split(value, delimiter):
    if value:
        return value.split(delimiter)
    return []


@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ""