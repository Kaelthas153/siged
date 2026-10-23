from django import forms
from django.contrib import admin
from django.db import transaction
from django.forms.models import model_to_dict
from accounts.roles import role_of
from config.admin_site import admin_site
from .models import AuditLog

class AdminReasonForm(forms.ModelForm):
    reason = forms.CharField(label='Motivo del cambio', min_length=5, max_length=400, widget=forms.Textarea(attrs={'rows': 2}))
    class Meta:
        fields = '__all__'

class RestrictedAdmin(admin.ModelAdmin):
    actions = None

    def has_module_permission(self, request):
        return role_of(request.user) == 'administrador'

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

class AuditedAdmin(RestrictedAdmin):
    form = AdminReasonForm

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            before = model_to_dict(type(obj).objects.get(pk=obj.pk)) if change else {}
            obj.save()
            AuditLog.objects.create(actor=request.user, entity=obj._meta.label_lower, record_id=obj.pk,
                                    action='modificar' if change else 'crear',
                                    detail={'motivo': form.cleaned_data['reason'], 'antes': before, 'despues': model_to_dict(obj)})

@admin.register(AuditLog, site=admin_site)
class AuditLogAdmin(RestrictedAdmin):
    list_display = ('created_at', 'actor', 'entity', 'record_id', 'action')
    readonly_fields = ('actor', 'entity', 'record_id', 'action', 'detail', 'created_at')
    list_filter = ('entity', 'action')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
