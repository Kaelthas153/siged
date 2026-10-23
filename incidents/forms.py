from django import forms
from django.utils import timezone
from .models import Zone, ThreatType

class IncidentForm(forms.Form):
    title = forms.CharField(label='Título del reporte', max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Ej. Deslizamiento simulado cerca de una vía'}))
    threat_type = forms.ModelChoiceField(label='Tipo de amenaza', queryset=ThreatType.objects.none(), empty_label='Selecciona un tipo')
    zone = forms.ModelChoiceField(label='Zona', queryset=Zone.objects.none(), empty_label='Selecciona una zona')
    occurred_at = forms.DateTimeField(label='Fecha y hora de ocurrencia', input_formats=['%Y-%m-%dT%H:%M'],
                                    help_text='Hora de La Paz. No puede estar en el futuro.', widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}))
    location_reference = forms.CharField(label='Referencia de ubicación', max_length=500, widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Describe un lugar ficticio que permita ubicar el reporte.'}))
    description = forms.CharField(label='Descripción', max_length=2000, widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Explica qué se observó en este escenario simulado.'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['zone'].queryset = Zone.objects.filter(active=True)
        self.fields['threat_type'].queryset = ThreatType.objects.filter(active=True)

    def clean_occurred_at(self):
        value = self.cleaned_data['occurred_at']
        if value > timezone.now():
            raise forms.ValidationError('La fecha de ocurrencia no puede ser futura.')
        return value
