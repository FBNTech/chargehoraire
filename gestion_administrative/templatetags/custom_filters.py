from django import template

register = template.Library()

@register.filter
def split(value, arg):
    """
    Returns the value split by arg.
    Example: {{ value|split:"/" }}
    """
    return value.split(arg)

@register.filter(name='dict_get')
def dict_get(dictionary, key):
    """
    Permet d'accéder à un élément d'un dictionnaire dans un template Django.
    Example: {{ my_dict|dict_get:key_variable }}
    """
    if dictionary and key:
        return dictionary.get(key, [])
    return []
