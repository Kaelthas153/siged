from django.contrib.admin import AdminSite
from accounts.roles import role_of

class SigedAdminSite(AdminSite):
    site_header = 'SIGED · Administración'
    site_title = 'SIGED'
    index_title = 'Cuentas, catálogos y auditoría'

    def has_permission(self, request):
        return request.user.is_active and request.user.is_staff and role_of(request.user) == 'administrador'

admin_site = SigedAdminSite(name='siged_admin')
