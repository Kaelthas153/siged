from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from audit.admin import RestrictedAdmin
from audit.models import AuditLog
from config.admin_site import admin_site
from .models import User
from .roles import ROLES, ROLE_LABELS, role_of

class FunctionalUserForm(forms.ModelForm):
    role = forms.ChoiceField(label='Rol funcional', choices=[(r, ROLE_LABELS[r]) for r in ROLES])
    new_password = forms.CharField(label='Nueva contraseña', required=False, widget=forms.PasswordInput,
                                   help_text='Obligatoria al crear. Déjala vacía para conservarla al editar.')
    reason = forms.CharField(label='Motivo del cambio', min_length=5, max_length=400, widget=forms.Textarea(attrs={'rows': 2}))
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk: self.fields['role'].initial = role_of(self.instance)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Ya existe una cuenta con ese correo.')
        return email

    def clean(self):
        data = super().clean()
        password = data.get('new_password')
        if not self.instance.pk and not password: self.add_error('new_password', 'Indica una contraseña.')
        if password:
            candidate = User(username=data.get('username', ''), first_name=data.get('first_name',''), last_name=data.get('last_name',''), email=data.get('email',''))
            try: validate_password(password, candidate)
            except ValidationError as exc: self.add_error('new_password', exc)
        if self.instance.pk and (not data.get('is_active') or data.get('role') != role_of(self.instance)):
            from tasks.models import Task
            if Task.objects.filter(assignee=self.instance, status__in=['pendiente','en_progreso']).exists():
                raise ValidationError('La cuenta tiene tareas abiertas. No se puede desactivar ni cambiar su rol.')
        return data

@admin.register(User, site=admin_site)
class FunctionalUserAdmin(RestrictedAdmin):
    form = FunctionalUserForm
    list_display = ('username', 'first_name', 'last_name', 'email', 'role_display', 'is_active')
    search_fields = ('username', 'email')
    fields = ('username', 'first_name', 'last_name', 'email', 'is_active', 'role', 'new_password', 'reason')

    @admin.display(description='Rol')
    def role_display(self, obj): return ROLE_LABELS.get(role_of(obj), 'Inválido')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_superuser=False)

    def get_form(self, request, obj=None, **kwargs):
        base = super().get_form(request, obj, **kwargs)
        class ScopedForm(base):
            def clean(self):
                data = super().clean()
                if self.instance.pk == request.user.pk and (not data.get('is_active') or data.get('role') != 'administrador'):
                    raise ValidationError('No puedes desactivar tu propia cuenta ni quitarte el rol administrador.')
                return data
        return ScopedForm

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            before = {}
            if change:
                old = User.objects.select_for_update().get(pk=obj.pk)
                before = {'username': old.username, 'email': old.email, 'activo': old.is_active, 'rol': role_of(old)}
            role = form.cleaned_data['role']
            obj.is_superuser = False
            obj.is_staff = role == 'administrador'
            if form.cleaned_data['new_password']: obj.set_password(form.cleaned_data['new_password'])
            obj.save()
            obj.groups.set([Group.objects.get(name=role)])
            obj.user_permissions.clear()
            AuditLog.objects.create(actor=request.user, entity='accounts.user', record_id=obj.pk, action='modificar' if change else 'crear',
                                    detail={'motivo': form.cleaned_data['reason'], 'antes': before,
                                            'despues': {'username': obj.username, 'email': obj.email, 'activo': obj.is_active, 'rol': role},
                                            'cambio_contrasena': bool(form.cleaned_data['new_password'])})
