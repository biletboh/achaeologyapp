from django import template
from django.utils.translation import ugettext as _


register = template.Library()


@register.filter
def object_attributes(obj, field):
    name = field.name
    try: 
        val = getattr(obj, name)
    except AttributeError:
        val = ""
    return val

