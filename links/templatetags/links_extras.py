from django import template

register = template.Library()


@register.filter
def getitem(obj, key):
    return obj.get(key, None)


@register.filter
def split(value, delimiter):
    return value.split(delimiter) 