from django.conf import settings
from django.db import models
from django.db.models import Q, F, Sum

class Resource(models.Model):
    code = models.CharField('código', max_length=20, unique=True)
    name = models.CharField('nombre', max_length=120)
    unit = models.CharField('unidad', max_length=30, default='unidad')
    total = models.PositiveIntegerField('cantidad total', default=0)
    active = models.BooleanField('activo', default=True)
    class Meta:
        ordering = ('name',)
        verbose_name = 'recurso reutilizable'
        verbose_name_plural = 'recursos reutilizables'
        constraints = [models.CheckConstraint(condition=Q(total__gte=0), name='resource_total_nonnegative')]
    def __str__(self): return self.name
    @property
    def reserved(self):
        return self.reservations.filter(released_at__isnull=True).aggregate(n=Sum('quantity'))['n'] or 0
    @property
    def available(self): return self.total - self.reserved

class Reservation(models.Model):
    incident = models.ForeignKey('incidents.Incident', on_delete=models.PROTECT, related_name='reservations')
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT, related_name='reservations')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='assigned_reservations')
    quantity = models.PositiveIntegerField()
    assigned_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    released_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='released_reservations', null=True, blank=True)
    class Meta:
        indexes = [models.Index(fields=['resource'], condition=Q(released_at__isnull=True), name='active_resource_reservations')]
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name='reservation_positive_quantity'),
            models.CheckConstraint(condition=Q(released_at__isnull=True, released_by__isnull=True) | Q(released_at__isnull=False, released_by__isnull=False), name='reservation_release_pair'),
            models.CheckConstraint(condition=Q(released_at__isnull=True) | Q(released_at__gte=F('assigned_at')), name='reservation_release_after_assignment'),
        ]
