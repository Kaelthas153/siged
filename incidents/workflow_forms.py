from django import forms
from django.db.models import Count
from django.utils import timezone
from accounts.models import User
from .models import Incident
from .forms import IncidentForm

class VersionForm(forms.Form):
    expected = forms.CharField(widget=forms.HiddenInput)

class ReviewForm(VersionForm):
    action = forms.ChoiceField(label='Decisión', choices=[('corregir','Solicitar corrección'),('validar','Validar información'),('rechazar','Rechazar reporte')])
    public_message = forms.CharField(label='Mensaje para el ciudadano', required=False, max_length=2000, widget=forms.Textarea(attrs={'rows':3}), help_text='Obligatorio para corrección y rechazo. No incluyas datos de otros reportantes.')
    reason = forms.CharField(label='Motivo interno del rechazo', required=False, max_length=2000, widget=forms.Textarea(attrs={'rows':3}))
    original_id = forms.IntegerField(label='ID del incidente original si es duplicado', required=False, min_value=1, help_text='Solo al rechazar. Consulta el ID en la ficha del original; no se comparte con el ciudadano.')
    def clean(self):
        data = super().clean()
        if data.get('action') in ('corregir','rechazar') and not data.get('public_message'):
            self.add_error('public_message','Escribe la explicación para el ciudadano.')
        if data.get('action') == 'rechazar' and not data.get('reason'): self.add_error('reason','Indica el motivo interno.')
        if data.get('original_id') and data.get('action') != 'rechazar': self.add_error('original_id','Solo se usa al rechazar un duplicado.')
        return data

class CorrectionForm(IncidentForm):
    expected = forms.CharField(widget=forms.HiddenInput)

class PriorityForm(VersionForm):
    priority = forms.ChoiceField(label='Prioridad', choices=Incident.Priority.choices)
    reason = forms.CharField(label='Motivo de la prioridad', max_length=2000, widget=forms.Textarea(attrs={'rows':3}))

class AssignmentForm(VersionForm):
    assignee = forms.ModelChoiceField(label='Operador responsable',queryset=User.objects.none())
    description = forms.CharField(label='Descripción de la tarea',max_length=2000,widget=forms.Textarea(attrs={'rows':4}))
    due_at = forms.DateTimeField(label='Fecha y hora de vencimiento',input_formats=['%Y-%m-%dT%H:%M'],widget=forms.DateTimeInput(attrs={'type':'datetime-local'}),help_text='Hora de La Paz; debe ser futura.')
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['assignee'].queryset=User.objects.filter(is_active=True,is_superuser=False).annotate(role_count=Count('groups')).filter(role_count=1,groups__name='operador').order_by('username')
    def clean_due_at(self):
        value=self.cleaned_data['due_at']
        if value <= timezone.now(): raise forms.ValidationError('El vencimiento debe ser futuro.')
        return value

class TaskActionForm(forms.Form):
    content = forms.CharField(label='Resultado o motivo',required=False,max_length=2000,widget=forms.Textarea(attrs={'rows':4}))
