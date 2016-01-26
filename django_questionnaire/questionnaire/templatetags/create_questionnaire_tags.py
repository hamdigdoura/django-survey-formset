from django import template

register = template.Library()


@register.filter
def get_error_choice(list_error, index):
    if index < len(list_error):
        return list_error[index].get('choice', '')
    return ''


@register.filter
def get_value(dictionary, key):
    return dictionary.get(key, {})