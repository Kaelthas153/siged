import uuid
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db import models
from django.db.models import Q, F

def incident_code():
    return 'SIG-' + uuid.uuid4().hex[:20].upper()

class Zone(models.Model):
    code = models.CharField('código', max_length=20, unique=True)
    name = models.CharField('nombre', max_length=120)
    municipality = models.CharField('municipio', max_length=100, default='La Paz')
    active = models.BooleanField('activa', default=True)
    class Meta:
        ordering = ('name',)
        verbose_name = 'zona'
        verbose_name_plural = 'zonas'
    def __str__(self): return self.name

class ThreatType(models.Model):
    name = models.CharField('nombre', max_length=80, unique=True)
    description = models.TextField('descripción', max_length=500)
    active = models.BooleanField('activo', default=True)
    class Meta:
        ordering = ('name',)
        verbose_name = 'tipo de amenaza'
        verbose_name_plural = 'tipos de amenaza'
    def __str__(self): return self.name

class Incident(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pendiente', 'Pendiente de revisión'
        CORRECTION = 'correccion_solicitada', 'Corrección solicitada'
        RESUBMITTED = 'reenviado', 'Reenviado'
        VALIDATED = 'validado', 'Validado'
        REJECTED = 'rechazado', 'Rechazado'
        FOLLOWING = 'en_seguimiento', 'En seguimiento'
        RESOLVED = 'resuelto', 'Resuelto'
        CLOSED = 'cerrado', 'Cerrado'

    class Priority(models.TextChoices):
        LOW = 'baja', 'Baja'
        MEDIUM = 'media', 'Media'
        HIGH = 'alta', 'Alta'
        CRITICAL = 'critica', 'Crítica'

    code = models.CharField(max_length=24, unique=True, default=incident_code, editable=False)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reported_incidents')
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT)
    threat_type = models.ForeignKey(ThreatType, on_delete=models.PROTECT)
    title = models.CharField(max_length=150, validators=[MinLengthValidator(1)])
    description = models.TextField(validators=[MinLengthValidator(1), MaxLengthValidator(2000)])
    location_reference = models.TextField(validators=[MinLengthValidator(1), MaxLengthValidator(500)])
    occurred_at = models.DateTimeField()
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField(editable=False)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=10, choices=Priority.choices, null=True, blank=True)
    resolution_summary = models.TextField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    duplicate_of = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        ordering = ('-created_at', '-pk')
        indexes = [models.Index(fields=['status', 'created_at']), models.Index(fields=['priority'])]
        constraints = [
            models.CheckConstraint(condition=Q(occurred_at__lte=F('created_at')), name='incident_occurred_before_registration'),
            models.CheckConstraint(condition=Q(updated_at__gte=F('created_at')), name='incident_update_after_creation'),
            models.CheckConstraint(condition=Q(status__in=['pendiente','correccion_solicitada','reenviado','validado','rechazado','en_seguimiento','resuelto','cerrado']), name='incident_valid_state'),
            models.CheckConstraint(condition=Q(priority__isnull=True) | Q(priority__in=['baja','media','alta','critica']), name='incident_valid_priority'),
            models.CheckConstraint(condition=~Q(status__in=['en_seguimiento','resuelto','cerrado']) | Q(priority__isnull=False), name='incident_following_has_priority'),
            models.CheckConstraint(condition=Q(duplicate_of__isnull=True) | (~Q(duplicate_of=F('pk')) & Q(status='rechazado')), name='incident_duplicate_not_self'),
            models.CheckConstraint(condition=(
                (~Q(status__in=['resuelto','cerrado']) & Q(resolved_at__isnull=True, closed_at__isnull=True, resolution_summary__isnull=True)) |
                (Q(status='resuelto', resolved_at__isnull=False, closed_at__isnull=True, resolution_summary__isnull=False) & ~Q(resolution_summary='') & Q(resolved_at__gte=F('created_at'))) |
                (Q(status='cerrado', resolved_at__isnull=False, closed_at__isnull=False, resolution_summary__isnull=False) & ~Q(resolution_summary='') & Q(resolved_at__gte=F('created_at'), closed_at__gte=F('resolved_at')))
            ), name='incident_resolution_dates'),
        ]
    def __str__(self): return self.code

class IncidentHistory(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.PROTECT, related_name='history')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=40)
    previous_status = models.CharField(max_length=24, null=True, blank=True)
    new_status = models.CharField(max_length=24, null=True, blank=True)
    detail = models.TextField()
    citizen_message = models.TextField(null=True, blank=True)
    task = models.ForeignKey('tasks.Task', on_delete=models.PROTECT, null=True, blank=True)
    reservation = models.ForeignKey('resources.Reservation', on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ('created_at', 'pk')
        indexes = [models.Index(fields=['incident', 'created_at'])]
        constraints = [models.CheckConstraint(condition=Q(task__isnull=True) | Q(reservation__isnull=True), name='history_one_related_object')]
