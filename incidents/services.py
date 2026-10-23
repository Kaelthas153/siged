from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from accounts.roles import require_role, role_of
from .models import Incident, IncidentHistory, Zone, ThreatType

def visible_incidents(user):
    require_role(user, 'ciudadano', 'operador', 'coordinador')
    qs = Incident.objects.select_related('zone', 'threat_type', 'reporter')
    return qs.filter(reporter=user) if role_of(user) == 'ciudadano' else qs

@transaction.atomic
def create_incident(*, user, data):
    require_role(user, 'ciudadano')
    now = timezone.now()
    zone = Zone.objects.select_for_update().get(pk=data['zone'].pk)
    threat = ThreatType.objects.select_for_update().get(pk=data['threat_type'].pk)
    if not zone.active or not threat.active:
        raise ValidationError('La zona o tipo seleccionado ya no está activo. Actualiza el formulario.')
    if data['occurred_at'] > now:
        raise ValidationError('La fecha de ocurrencia no puede ser futura.')
    obj = Incident(reporter=user, zone=zone, threat_type=threat,
                   title=data['title'].strip(), description=data['description'].strip(),
                   location_reference=data['location_reference'].strip(), occurred_at=data['occurred_at'],
                   created_at=now, updated_at=now)
    obj.full_clean()
    obj.save()
    IncidentHistory.objects.create(incident=obj, actor=user, action='registrar', new_status=obj.status,
                                   detail='Registro inicial del incidente.',
                                   citizen_message='Recibimos tu reporte. Está pendiente de revisión de información.')
    return obj
