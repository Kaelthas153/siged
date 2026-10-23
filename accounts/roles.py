from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

ROLES = ('ciudadano', 'operador', 'coordinador', 'administrador')
ROLE_LABELS = {'ciudadano': 'Ciudadano', 'operador': 'Operador', 'coordinador': 'Coordinador', 'administrador': 'Administrador'}

def role_of(user):
    if not user.is_authenticated or not user.is_active or user.is_superuser:
        return None
    roles = list(user.groups.values_list('name', flat=True))
    return roles[0] if len(roles) == 1 and roles[0] in ROLES else None

def require_role(user, *allowed):
    if role_of(user) not in allowed:
        raise PermissionDenied('Tu cuenta no tiene permiso para esta acción.')

def roles_required(*allowed):
    def decorate(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            require_role(request.user, *allowed)
            return view(request, *args, **kwargs)
        return wrapped
    return decorate
