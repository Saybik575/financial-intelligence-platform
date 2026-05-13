from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def indian_currency(value):

    if value is None:
        return ""

    try:
        value = int(value)
    except (ValueError, TypeError):
        return value

    num = str(value)

    if len(num) <= 3:
        return num

    last3 = num[-3:]

    remaining = num[:-3]

    parts = []

    while len(remaining) > 2:
        parts.insert(0, remaining[-2:])
        remaining = remaining[:-2]

    if remaining:
        parts.insert(0, remaining)

    return ",".join(parts) + "," + last3