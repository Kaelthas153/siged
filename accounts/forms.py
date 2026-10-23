from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .roles import role_of

class RoleAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if role_of(user) is None:
            raise ValidationError('La cuenta debe tener exactamente un rol funcional válido. Consulta al administrador.', code='invalid_role')
