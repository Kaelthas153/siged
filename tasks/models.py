from django.conf import settings
from django.db import models
from django.db.models import Q, F

class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pendiente', 'Pendiente'
        PROGRESS = 'en_progreso', 'En progreso'
        COMPLETED = 'completada', 'Completada'
        CANCELLED = 'cancelada', 'Cancelada'
    incident = models.ForeignKey('incidents.Incident', on_delete=models.PROTECT, related_name='tasks')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='assigned_tasks')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_tasks')
    description = models.TextField()
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    due_at = models.DateTimeField()
    created_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    result = models.TextField(null=True, blank=True)
    class Meta:
        indexes = [models.Index(fields=['assignee', 'status'])]
        constraints = [
            models.CheckConstraint(condition=Q(status__in=['pendiente','en_progreso','completada','cancelada']), name='task_valid_state'),
            models.CheckConstraint(condition=Q(due_at__gte=F('created_at')), name='task_due_after_creation'),
            models.CheckConstraint(condition=Q(started_at__isnull=True) | Q(started_at__gte=F('created_at')), name='task_start_after_creation'),
            models.CheckConstraint(condition=Q(finished_at__isnull=True) | Q(finished_at__gte=F('created_at')), name='task_finish_after_creation'),
            models.CheckConstraint(condition=Q(started_at__isnull=True) | Q(finished_at__isnull=True) | Q(finished_at__gte=F('started_at')), name='task_finish_after_start'),
            models.CheckConstraint(condition=(
                Q(status='pendiente', started_at__isnull=True, finished_at__isnull=True) |
                Q(status='en_progreso', started_at__isnull=False, finished_at__isnull=True) |
                (Q(status='completada', started_at__isnull=False, finished_at__isnull=False, result__isnull=False) & ~Q(result='')) |
                Q(status='cancelada', finished_at__isnull=False)
            ), name='task_dates_match_state'),
        ]
