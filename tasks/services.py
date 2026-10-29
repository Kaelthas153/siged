from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from accounts.models import User
from accounts.roles import require_role, role_of
from incidents.models import Incident
from incidents.workflow import OPERABLE, record, text_required, check_version
from .models import Task

@transaction.atomic
def assign_task(*, user, incident_id, assignee_id, description, due_at, expected=None):
    require_role(user, 'coordinador')
    incident = get_object_or_404(Incident.objects.select_for_update(), pk=incident_id)
    check_version(incident, expected)
    if incident.status not in OPERABLE: raise ValidationError('Solo se asignan tareas a incidentes validados o en seguimiento.')
    assignee = get_object_or_404(User.objects.select_for_update(), pk=assignee_id)
    if role_of(assignee) != 'operador': raise ValidationError('Selecciona un operador activo con un único rol.')
    now = timezone.now()
    if due_at <= now: raise ValidationError('El vencimiento debe estar en el futuro.')
    task = Task(incident=incident, assignee=assignee, created_by=user,
                description=text_required(description, 'Descripción', 2000), due_at=due_at, created_at=now)
    task.full_clean(); task.save()
    record(incident, user, 'asignar_tarea', incident.status, f'Tarea {task.pk} asignada a {assignee.display_name}.', task=task)
    return task

@transaction.atomic
def act_on_task(*, user, pk, action, content=''):
    require_role(user, 'operador', 'coordinador')
    scope = Task.objects.all()
    if role_of(user) == 'operador': scope = scope.filter(assignee=user)
    reference = get_object_or_404(scope, pk=pk)
    incident = get_object_or_404(Incident.objects.select_for_update(), pk=reference.incident_id)
    task = Task.objects.select_for_update().get(pk=pk)
    if incident.status not in OPERABLE: raise ValidationError('El incidente no permite acciones sobre tareas.')
    if task.status not in ('pendiente','en_progreso'): raise ValidationError('Las tareas terminadas no se modifican.')
    now = timezone.now()
    if action == 'iniciar':
        require_role(user, 'operador')
        if task.assignee_id != user.pk: raise PermissionDenied
        if task.status != 'pendiente' or incident.status != 'en_seguimiento':
            raise ValidationError('Se inicia una tarea pendiente cuando el incidente está en seguimiento.')
        task.status, task.started_at = 'en_progreso', now
        detail = f'Tarea {task.pk} iniciada.'
    elif action == 'completar':
        require_role(user, 'operador')
        if task.assignee_id != user.pk: raise PermissionDenied
        if task.status != 'en_progreso' or incident.status != 'en_seguimiento':
            raise ValidationError('Primero debes iniciar la tarea dentro de un incidente en seguimiento.')
        task.result = text_required(content, 'Resultado', 2000)
        task.status, task.finished_at = 'completada', now
        detail = f'Tarea {task.pk} completada. Resultado: {task.result}'
    elif action == 'cancelar':
        require_role(user, 'coordinador')
        reason = text_required(content, 'Motivo de cancelación', 2000)
        task.status, task.finished_at = 'cancelada', now
        detail = f'Tarea {task.pk} cancelada. Motivo: {reason}'
    else: raise ValidationError('Acción de tarea inválida.')
    task.full_clean(); task.save()
    record(incident, user, action+'_tarea', incident.status, detail, task=task)
    return task
