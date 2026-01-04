from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Permet d'accéder à une valeur d'un dictionnaire par sa clé dans un template Django.
    Utilisation : {{ my_dict|get_item:key }}
    """
    return dictionary.get(key, key)
