import secrets
from pathlib import Path
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from accounts.models import User
from accounts.roles import ROLES
from incidents.models import Zone, ThreatType
from incidents.services import create_incident
from resources.models import Resource
from audit.models import AuditLog

class Command(BaseCommand):
    help = 'Crea cuatro roles, cuentas y catálogos ficticios. No reinicia contraseñas ni borra datos existentes.'

    @transaction.atomic
    def handle(self, *args, **options):
        credentials = []
        users = {}
        for role in ROLES:
            group, _ = Group.objects.get_or_create(name=role)
            user, created = User.objects.get_or_create(username=role, defaults={'email': f'{role}@siged.example', 'first_name': role.capitalize(), 'last_name': 'Demo', 'is_staff': role == 'administrador'})
            if created:
                password = secrets.token_urlsafe(13) + '7!'
                user.set_password(password); user.save(); user.groups.set([group])
                credentials.append(f'{role}: {password}')
            users[role] = user
        admin = users['administrador']
        for n in range(1, 6):
            zone, created = Zone.objects.get_or_create(code=f'Z{n:02}', defaults={'name': f'Zona de demostración {n}', 'municipality': 'La Paz'})
            if created: AuditLog.objects.create(actor=admin, entity='incidents.zone', record_id=zone.pk, action='carga_demo', detail={'motivo': 'Carga inicial ficticia'})
        for name in ['Deslizamiento', 'Inundación', 'Incendio forestal']:
            threat, created = ThreatType.objects.get_or_create(name=name, defaults={'description': f'Categoría ilustrativa de {name.lower()}.'})
            if created: AuditLog.objects.create(actor=admin, entity='incidents.threattype', record_id=threat.pk, action='carga_demo', detail={'motivo': 'Carga inicial ficticia'})
        for n, name in enumerate(['Linterna reutilizable', 'Radio portátil', 'Casco reutilizable', 'Chaleco reflectante', 'Equipo de inspección simulado'], 1):
            resource, created = Resource.objects.get_or_create(code=f'R{n:02}', defaults={'name': name, 'total': 5, 'unit': 'unidad'})
            if created: AuditLog.objects.create(actor=admin, entity='resources.resource', record_id=resource.pk, action='carga_demo', detail={'motivo': 'Carga inicial ficticia', 'total': 5})
        citizen = users['ciudadano']
        if not citizen.reported_incidents.exists():
            create_incident(user=citizen, data={'title': 'Reporte de práctica en una vía ficticia', 'description': 'Escenario de demostración: se observa material sobre una vía. No representa un evento real.',
                                              'location_reference': 'Cruce ilustrativo A, sector de prueba.', 'zone': Zone.objects.first(), 'threat_type': ThreatType.objects.first(),
                                              'occurred_at': timezone.now() - timedelta(hours=1)})
        if credentials:
            target = Path(settings.BASE_DIR) / '.demo-credentials.txt'
            previous = target.read_text(encoding='utf-8') if target.exists() else 'CUENTAS LOCALES DE PRUEBA · NO COMPARTIR ESTE ARCHIVO\n'
            payload = previous + '\n'.join(credentials) + '\n'
            transaction.on_commit(lambda: target.write_text(payload, encoding='utf-8'))
        self.stdout.write(self.style.SUCCESS('Datos ficticios preparados. Las contraseñas nuevas se guardan localmente en .demo-credentials.txt.'))
