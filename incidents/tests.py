from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from datetime import timedelta
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import connections, IntegrityError, transaction
from django.utils import timezone
from accounts.models import User
from accounts.roles import ROLES
from audit.models import AuditLog
from resources.models import Resource, Reservation
from resources.prototype import reserve_prototype
from .models import Zone, ThreatType, Incident, IncidentHistory
from .services import create_incident

def fixtures():
    users={}
    for role in ROLES:
        group,_=Group.objects.get_or_create(name=role)
        user=User.objects.create_user(role,email=role+'@example.test',password='Prueba-Segura-8391!',is_staff=role=='administrador')
        user.groups.add(group);users[role]=user
    other=User.objects.create_user('otro',email='otro@example.test',password='Prueba-Segura-8391!')
    other.groups.add(Group.objects.get(name='ciudadano'));users['otro']=other
    zone=Zone.objects.create(code='Z1',name='Zona ficticia')
    threat=ThreatType.objects.create(name='Inundación',description='Ejemplo')
    data=dict(zone=zone,threat_type=threat,title='Reporte de prueba',description='Datos ficticios',location_reference='Calle ficticia',occurred_at=timezone.now()-timedelta(hours=1))
    return users,data

class WeekOneTests(TestCase):
    @classmethod
    def setUpTestData(cls): cls.users,cls.data=fixtures()
    def incident(self,who='ciudadano'): return create_incident(user=self.users[who],data=self.data)
    def login(self,role='ciudadano'): self.client.force_login(self.users[role])
    def post_data(self):
        return {**self.data,'zone':self.data['zone'].pk,'threat_type':self.data['threat_type'].pk,'occurred_at':timezone.localtime(self.data['occurred_at']).strftime('%Y-%m-%dT%H:%M')}
    def test_anonymous_redirect(self): self.assertEqual(self.client.get('/incidentes/').status_code,302)
    def test_login_and_logout(self):
        self.assertTrue(self.client.login(username='ciudadano',password='Prueba-Segura-8391!'))
        self.assertEqual(self.client.get('/incidentes/').status_code,200)
        self.assertEqual(self.client.get('/salir/').status_code,405)
        self.assertEqual(self.client.post('/salir/').status_code,302)
    def test_own_records_only(self):
        own=self.incident();other=self.incident('otro');self.login()
        response=self.client.get('/incidentes/')
        self.assertContains(response,own.code);self.assertNotContains(response,other.code)
        self.assertEqual(self.client.get(f'/incidentes/{other.pk}/').status_code,404)
    def test_server_controls_identity_and_state(self):
        self.login();data=self.post_data();data.update(reporter=self.users['otro'].pk,status='cerrado',priority='critica')
        self.assertEqual(self.client.post('/incidentes/nuevo/',data).status_code,302)
        obj=Incident.objects.get();self.assertEqual(obj.reporter,self.users['ciudadano']);self.assertEqual(obj.status,'pendiente');self.assertIsNone(obj.priority)
        self.assertEqual(obj.history.count(),1)
    def test_future_rejected(self):
        self.login();data=self.post_data();data['occurred_at']=(timezone.localtime()+timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        self.assertEqual(self.client.post('/incidentes/nuevo/',data).status_code,200);self.assertFalse(Incident.objects.exists())
    def test_inactive_catalog_rejected(self):
        Zone.objects.update(active=False);self.login()
        self.client.post('/incidentes/nuevo/',self.post_data());self.assertFalse(Incident.objects.exists())
    def test_empty_description_rejected(self):
        self.login();data=self.post_data();data['description']='   '
        self.client.post('/incidentes/nuevo/',data);self.assertFalse(Incident.objects.exists())
    def test_atomic_history(self):
        with patch('incidents.services.IncidentHistory.objects.create',side_effect=RuntimeError('Fallo simulado')):
            with self.assertRaises(RuntimeError): self.incident()
        self.assertFalse(Incident.objects.exists())
    def test_private_history_hidden(self):
        obj=self.incident();IncidentHistory.objects.create(incident=obj,actor=self.users['operador'],action='nota',detail='NOTA_INTERNA_SECRETA')
        self.login();self.assertNotContains(self.client.get(f'/incidentes/{obj.pk}/'),'NOTA_INTERNA_SECRETA')
    def test_html_escaped(self):
        self.data['description']='<script>alert(1)</script>';obj=self.incident();self.login()
        r=self.client.get(f'/incidentes/{obj.pk}/');self.assertNotContains(r,'<script>alert(1)</script>');self.assertContains(r,'&lt;script&gt;')
    def test_operational_permissions(self):
        for role in ('operador','coordinador'):
            self.login(role);self.assertEqual(self.client.get('/incidentes/').status_code,200)
            self.assertEqual(self.client.post('/incidentes/nuevo/',self.post_data()).status_code,403)
            self.assertEqual(self.client.get('/administracion/').status_code,302)
    def test_admin_separation(self):
        self.login('administrador');self.assertEqual(self.client.get('/administracion/').status_code,200)
        self.assertEqual(self.client.get('/incidentes/').status_code,403)
    def test_invalid_multiple_roles(self):
        self.users['ciudadano'].groups.add(Group.objects.get(name='operador'));self.login()
        self.assertEqual(self.client.get('/incidentes/').status_code,403)
        self.client.logout();r=self.client.post('/ingresar/',{'username':'ciudadano','password':'Prueba-Segura-8391!'})
        self.assertEqual(r.status_code,200);self.assertNotIn('_auth_user_id',self.client.session)
    def test_csrf_enforced(self):
        c=Client(enforce_csrf_checks=True);c.force_login(self.users['ciudadano'])
        self.assertEqual(c.post('/incidentes/nuevo/',self.post_data()).status_code,403)
    def test_database_state_constraint(self):
        obj=self.incident()
        with self.assertRaises(IntegrityError),transaction.atomic(): Incident.objects.filter(pk=obj.pk).update(status='inventado')
    def test_admin_creation_audited_and_escalation_ignored(self):
        self.login('administrador')
        data={'username':'nuevo','first_name':'Nueva','last_name':'Cuenta','email':'nueva@example.test','is_active':'on','role':'ciudadano','new_password':'Otra-Clave-83911!','reason':'Alta de demostración','is_superuser':'on','is_staff':'on'}
        r=self.client.post('/administracion/accounts/user/add/',data)
        self.assertEqual(r.status_code,302)
        user=User.objects.get(username='nuevo');self.assertFalse(user.is_superuser);self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password(data['new_password']))
        audit=AuditLog.objects.get(entity='accounts.user',record_id=user.pk)
        self.assertNotIn(data['new_password'],str(audit.detail));self.assertNotIn(user.password,str(audit.detail))
    def test_catalog_audit_and_delete_denial(self):
        self.login('administrador')
        r=self.client.post('/administracion/incidents/zone/add/',{'code':'Z2','name':'Otra zona','municipality':'La Paz','active':'on','reason':'Ejemplo académico'})
        self.assertEqual(r.status_code,302);obj=Zone.objects.get(code='Z2')
        self.assertTrue(AuditLog.objects.filter(entity='incidents.zone',record_id=obj.pk).exists())
        self.assertEqual(self.client.post(f'/administracion/incidents/zone/{obj.pk}/delete/',{'post':'yes'}).status_code,403)

class StockConcurrencyTests(TransactionTestCase):
    def test_two_requests_cannot_overbook(self):
        users,data=fixtures();resource=Resource.objects.create(code='R1',name='Recurso ficticio',unit='unidad',total=5)
        incidents=[create_incident(user=users['ciudadano'],data=data) for _ in range(2)]
        Incident.objects.update(status='validado')
        barrier=Barrier(2)
        def reserve(incident):
            connections.close_all()
            try:
                user=User.objects.get(pk=users['coordinador'].pk);barrier.wait(timeout=10)
                try:
                    reserve_prototype(user=user,incident_id=incident.pk,resource_id=resource.pk,quantity=4)
                    return 'aceptada'
                except ValidationError: return 'rechazada'
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(reserve,incidents))
        self.assertCountEqual(results,['aceptada','rechazada']);self.assertEqual(Reservation.objects.count(),1)
        resource.refresh_from_db();self.assertEqual(resource.available,1)
        self.assertEqual(IncidentHistory.objects.filter(action='reservar_recurso').count(),1)
