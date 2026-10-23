"""Prueba técnica de semana 1. Sin rutas públicas de reserva hasta semana 3."""
from django.core.exceptions import ValidationError
from django.db import transaction
from accounts.roles import require_role
from incidents.models import Incident, IncidentHistory
from .models import Resource, Reservation

@transaction.atomic
def reserve_prototype(*, user, incident_id, resource_id, quantity):
    require_role(user, 'coordinador')
    if type(quantity) is not int or quantity <= 0:
        raise ValidationError('La cantidad debe ser un entero positivo.')
    incident = Incident.objects.select_for_update().get(pk=incident_id)
    if incident.status not in (Incident.Status.VALIDATED, Incident.Status.FOLLOWING):
        raise ValidationError('El incidente debe estar validado o en seguimiento.')
    resource = Resource.objects.select_for_update().get(pk=resource_id)
    if not resource.active or quantity > resource.available:
        raise ValidationError('No hay suficientes unidades disponibles.')
    reservation = Reservation.objects.create(incident=incident, resource=resource, assigned_by=user, quantity=quantity)
    IncidentHistory.objects.create(incident=incident, actor=user, action='reservar_recurso', reservation=reservation,
                                   detail=f'Reserva técnica de {quantity} unidades del recurso {resource.code}.')
    return reservation
