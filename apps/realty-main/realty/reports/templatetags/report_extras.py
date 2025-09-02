from django import template

register = template.Library()


@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, None)


@register.filter
def percent_change(current, previous):
    try:
        c = float(current)
        print(c)
        p = float(previous)
        print(p)
        if p == 0:
            return None
        print((c / p - 1) * 100)
        print("f")
        return (c / p - 1) * 100
    except Exception:
        return None


@register.filter
def percent_change2(current, previous):
    try:
        current = float(current)
        previous = float(previous)
    except (TypeError, ValueError):
        return "—"
    if previous == 0:
        return "—"
    return f"{(current - previous) / previous * 100:.1f}%"
