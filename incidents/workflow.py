"""Transiciones operativas. Toda escritura bloquea el incidente e incluye su historial."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from accounts.models import User
from accounts.roles import require_role, role_of
from .models import Incident, IncidentHistory, Zone, ThreatType

REVIEWABLE = ('pendiente', 'reenviado')
OPERABLE = ('validado', 'en_seguimiento')

def text_required(value, label, limit=2000):
    value = (value or '').strip()
    if not value or len(value) > limit:
        raise ValidationError(f'{label}: escribe entre 1 y {limit} caracteres.')
    return value

def check_version(obj, expected):
    if expected and obj.updated_at.isoformat() != expected:
        raise ValidationError('El reporte cambió mientras lo revisabas. Vuelve a la ficha y revisa su estado actual.')

def record(obj, user, action, before, detail, public=None, task=None):
    obj.updated_at = timezone.now()
    obj.full_clean()
    obj.save()
    IncidentHistory.objects.create(incident=obj, actor=user, action=action,
        previous_status=before, new_status=obj.status, detail=detail, citizen_message=public, task=task)

@transaction.atomic
def review(*, user, pk, action, reason='', public_message='', original_id=None, expected=None):
    require_role(user, 'operador')
    ids = sorted({pk, original_id} - {None})
    locked = {i.pk: i for i in Incident.objects.select_for_update().filter(pk__in=ids).order_by('pk')}
    obj = locked.get(pk)
    if obj is None: return get_object_or_404(Incident, pk=pk)
    check_version(obj, expected)
    if obj.status not in REVIEWABLE:
        raise ValidationError('Solo se revisan reportes pendientes o reenviados.')
    before = obj.status
    if action == 'corregir':
        public_message = text_required(public_message, 'Observación para el ciudadano')
        obj.status = 'correccion_solicitada'
        detail = public_message
    elif action == 'validar':
        if original_id: raise ValidationError('El original solo se indica al rechazar un duplicado.')
        obj.status = 'validado'
        detail = 'Información revisada y validada para la simulación.'
        public_message = 'Tu reporte fue revisado y validado.'
    elif action == 'rechazar':
        reason = text_required(reason, 'Motivo interno')
        public_message = text_required(public_message, 'Explicación para el ciudadano')
        if original_id:
            original = locked.get(original_id)
            if not original or original.pk == obj.pk or original.status not in ('validado','en_seguimiento','resuelto','cerrado') or original.duplicate_of_id:
                raise ValidationError('El original debe ser otro incidente validado, en seguimiento, resuelto o cerrado, sin referencia de duplicado.')
            obj.duplicate_of = original
            reason += f' Original interno: {original.code}.'
        obj.status = 'rechazado'
        detail = reason
    else:
        raise ValidationError('Acción de revisión inválida.')
    if original_id and action != 'rechazar':
        raise ValidationError('Solo el rechazo permite marcar un duplicado.')
    record(obj, user, action, before, detail, public_message)
    return obj

@transaction.atomic
def resubmit(*, user, pk, data, expected=None):
    require_role(user, 'ciudadano')
    obj = get_object_or_404(Incident.objects.select_for_update(), pk=pk, reporter=user)
    check_version(obj, expected)
    if obj.status != 'correccion_solicitada':
        raise ValidationError('Solo puedes corregir un reporte cuando el operador lo solicita.')
    zone = Zone.objects.select_for_update().get(pk=data['zone'].pk)
    threat = ThreatType.objects.select_for_update().get(pk=data['threat_type'].pk)
    if not zone.active or not threat.active: raise ValidationError('Selecciona catálogos activos.')
    if data['occurred_at'] > obj.created_at:
        raise ValidationError('La ocurrencia no puede ser posterior al registro original del reporte.')
    before = obj.status
    obj.zone, obj.threat_type = zone, threat
    for name, limit in [('title',150), ('description',2000), ('location_reference',500)]:
        setattr(obj, name, text_required(data[name], 'Contenido', limit))
    obj.occurred_at = data['occurred_at']
    obj.status = 'reenviado'
    record(obj, user, 'reenviar', before, 'El ciudadano corrigió y reenvió el reporte.', 'Corrección enviada. Tu reporte espera una nueva revisión.')
    return obj

@transaction.atomic
def prioritize(*, user, pk, priority, reason, expected=None):
    require_role(user, 'coordinador')
    obj = get_object_or_404(Incident.objects.select_for_update(), pk=pk)
    check_version(obj, expected)
    if obj.status not in OPERABLE: raise ValidationError('La prioridad se define en reportes validados o en seguimiento.')
    if priority not in Incident.Priority.values: raise ValidationError('Prioridad inválida.')
    reason = text_required(reason, 'Motivo de prioridad')
    previous = obj.priority or 'sin prioridad'
    obj.priority = priority
    record(obj, user, 'priorizar', obj.status, f'{previous} → {priority}. {reason}')
    return obj

@transaction.atomic
def start_following(*, user, pk, expected=None):
    require_role(user, 'coordinador')
    obj = get_object_or_404(Incident.objects.select_for_update(), pk=pk)
    check_version(obj, expected)
    if obj.status != 'validado' or not obj.priority:
        raise ValidationError('Se requiere un reporte validado con prioridad.')
    assignee_ids = obj.tasks.filter(status='pendiente').values_list('assignee_id', flat=True)
    operators = User.objects.select_for_update().filter(pk__in=assignee_ids).order_by('pk')
    if not any(role_of(operator) == 'operador' for operator in operators):
        raise ValidationError('Asigna al menos una tarea pendiente a un operador activo.')
    obj.status = 'en_seguimiento'
    record(obj, user, 'iniciar_seguimiento', 'validado', 'Coordinación inició el seguimiento.', 'Se inició el seguimiento de tu reporte.')
    return obj
