from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Acessa o valor de um dicionário pela chave no template."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
