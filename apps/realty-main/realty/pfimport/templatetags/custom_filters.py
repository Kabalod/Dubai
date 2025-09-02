from django import template

register = template.Library()


@register.filter
def roi_display(value):
    try:
        if value is None:
            return "—"
        if float(value) == 0.0:
            return "—"
        if 0.0 < abs(float(value)) < 0.0005:
            return f"{value:.6f}"
        return f"{value:.3f}"
    except Exception:
        return "—"
