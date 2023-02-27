from django import template

register = template.Library()


@register.filter
def addclass(fields, css):
    return fields.as_widget(attrs={'class': css})
