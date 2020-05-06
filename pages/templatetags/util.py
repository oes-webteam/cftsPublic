from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def get_type( value ):
    return type( value )

@register.filter
@stringfilter
def split( value, key ):
  return value.split( key )