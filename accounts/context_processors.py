from .roles import role_of, ROLE_LABELS

def role_context(request):
    role = role_of(request.user)
    return {'functional_role': role, 'role_label': ROLE_LABELS.get(role, 'Sin rol válido')}
