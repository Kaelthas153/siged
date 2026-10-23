from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .roles import require_role, ROLES, role_of

@login_required
def home(request):
    require_role(request.user, *ROLES)
    if role_of(request.user) == 'administrador':
        return redirect('siged_admin:index')
    return redirect('incidents:list')
