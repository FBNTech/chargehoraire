from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, css_class):
    """Ajoute une classe CSS à un widget de formulaire."""
    if value.field.widget.attrs.get('class', ''):
        value.field.widget.attrs['class'] += f' {css_class}'
    else:
        value.field.widget.attrs['class'] = css_class
    return value
