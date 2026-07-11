from django import template


register = template.Library()


@register.filter
def has_role_permission(user, codename):
    if not getattr(user, "is_authenticated", False):
        return False
    return user.has_role_permission(codename)


@register.simple_tag(takes_context=True)
def query_string(context, **updates):
    query = context["request"].GET.copy()
    for key, value in updates.items():
        if value in (None, ""):
            query.pop(key, None)
        else:
            query[key] = value
    return query.urlencode()
