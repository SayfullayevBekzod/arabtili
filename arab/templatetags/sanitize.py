from django import template

register = template.Library()

@register.filter
def safe_text(value):
    """
    Sanitizes value for UI display.
    Returns empty string if value is None, "None", or empty.
    """
    if value in [None, "", "None"]:
        return ""
    return value
