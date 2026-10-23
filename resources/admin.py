from django.contrib import admin
from django.core.exceptions import ValidationError
from config.admin_site import admin_site
from audit.admin import AuditedAdmin, AdminReasonForm
from .models import Resource

class ResourceForm(AdminReasonForm):
    class Meta(AdminReasonForm.Meta):
        model = Resource

    def clean(self):
        data = super().clean()
        if self.instance.pk:
            # Django Admin envuelve el formulario POST en una transacción.
            obj = Resource.objects.select_for_update().get(pk=self.instance.pk)
            if data.get('total', obj.total) < obj.reserved:
                raise ValidationError('El total no puede ser menor que la cantidad reservada.')
            if not data.get('active', obj.active) and obj.reserved:
                raise ValidationError('No puedes desactivar un recurso con reservas activas.')
        return data

@admin.register(Resource, site=admin_site)
class ResourceAdmin(AuditedAdmin):
    form = ResourceForm
    list_display = ('code', 'name', 'total', 'reserved_display', 'available_display', 'active')
    readonly_fields = ('reserved_display', 'available_display')
    @admin.display(description='Reservado')
    def reserved_display(self, obj): return obj.reserved if obj.pk else 0
    @admin.display(description='Disponible')
    def available_display(self, obj): return obj.available if obj.pk else 0
