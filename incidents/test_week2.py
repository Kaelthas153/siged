from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch
from django.test import TestCase, TransactionTestCase, Client
from django.db import connections
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.contrib.auth.models import Group
from django.utils import timezone
from accounts.models import User
from tasks.models import Task
from tasks.services import assign_task, act_on_task
from .tests import fixtures
from .models import Incident, IncidentHistory
from .services import create_incident
from .workflow import review, resubmit, prioritize, start_following

class WeekTwoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users,cls.data=fixtures()
        cls.other_operator=User.objects.create_user('operador2',email='op2@example.test',password='Prueba-segura-7481!')
        cls.other_operator.groups.add(Group.objects.get(name='operador'))
    def new(self): return create_incident(user=self.users['ciudadano'],data=self.data)
    def valid(self):
        obj=self.new();return review(user=self.users['operador'],pk=obj.pk,action='validar')
    def task(self,obj):return assign_task(user=self.users['coordinador'],incident_id=obj.pk,assignee_id=self.users['operador'].pk,description='Inspección ficticia',due_at=timezone.now()+timedelta(days=1))
    def following(self):
        obj=self.valid();prioritize(user=self.users['coordinador'],pk=obj.pk,priority='alta',reason='Criterio simulado')
        task=self.task(obj);start_following(user=self.users['coordinador'],pk=obj.pk)
        return obj,task
    def test_correction_resubmission_validation_preserves_identity(self):
        obj=self.new();created,code,reporter=obj.created_at,obj.code,obj.reporter_id
        review(user=self.users['operador'],pk=obj.pk,action='corregir',public_message='Aclara la ubicación')
        data={**self.data,'location_reference':'Ubicación ficticia ampliada','reporter':self.users['otro'],'status':'cerrado'}
        corrected=resubmit(user=self.users['ciudadano'],pk=obj.pk,data=data)
        self.assertEqual(corrected.status,'reenviado');self.assertEqual(corrected.created_at,created)
        self.assertEqual(corrected.code,code);self.assertEqual(corrected.reporter_id,reporter)
        review(user=self.users['operador'],pk=obj.pk,action='validar')
        obj.refresh_from_db();self.assertEqual(obj.status,'validado');self.assertEqual(obj.history.count(),4)
    def test_review_role_and_required_observation(self):
        obj=self.new()
        with self.assertRaises(PermissionDenied):review(user=self.users['coordinador'],pk=obj.pk,action='validar')
        with self.assertRaises(ValidationError):review(user=self.users['operador'],pk=obj.pk,action='corregir',public_message=' ')
        obj.refresh_from_db();self.assertEqual(obj.status,'pendiente')
    def test_rejection_public_private_separation_and_terminal(self):
        obj=self.new();review(user=self.users['operador'],pk=obj.pk,action='rechazar',reason='MOTIVO_INTERNO',public_message='No corresponde al alcance')
        self.client.force_login(self.users['ciudadano']);r=self.client.get(f'/incidentes/{obj.pk}/')
        self.assertContains(r,'No corresponde al alcance');self.assertNotContains(r,'MOTIVO_INTERNO')
        with self.assertRaises(ValidationError):review(user=self.users['operador'],pk=obj.pk,action='validar')
    def test_rejection_requires_both_messages(self):
        obj=self.new()
        for reason,public in [('motivo',''),('','explicación')]:
            with self.assertRaises(ValidationError):review(user=self.users['operador'],pk=obj.pk,action='rechazar',reason=reason,public_message=public)
        self.assertEqual(obj.history.count(),1)
    def test_duplicate_original_constraints(self):
        obj=self.new();pending=self.new()
        for original in (obj.pk,pending.pk,99999):
            with self.assertRaises(ValidationError):review(user=self.users['operador'],pk=obj.pk,action='rechazar',reason='Duplicado',public_message='Reporte repetido',original_id=original)
        original=self.valid();review(user=self.users['operador'],pk=obj.pk,action='rechazar',reason='Duplicado',public_message='Reporte repetido',original_id=original.pk)
        obj.refresh_from_db();self.assertEqual(obj.duplicate_of_id,original.pk)
        self.client.force_login(self.users['ciudadano']);self.assertNotContains(self.client.get(f'/incidentes/{obj.pk}/'),original.code)
    def test_foreign_correction_and_state_rejected(self):
        obj=self.new()
        with self.assertRaises(ValidationError):resubmit(user=self.users['ciudadano'],pk=obj.pk,data=self.data)
        review(user=self.users['operador'],pk=obj.pk,action='corregir',public_message='Amplía el reporte')
        with self.assertRaises(Http404):resubmit(user=self.users['otro'],pk=obj.pk,data=self.data)
    def test_correction_invalid_date_rolls_back(self):
        obj=self.new();review(user=self.users['operador'],pk=obj.pk,action='corregir',public_message='Amplía el reporte')
        with self.assertRaises(ValidationError):resubmit(user=self.users['ciudadano'],pk=obj.pk,data={**self.data,'occurred_at':timezone.now()+timedelta(days=1),'title':'CAMBIO'})
        obj.refresh_from_db();self.assertEqual(obj.title,self.data['title']);self.assertEqual(obj.status,'correccion_solicitada')
    def test_review_and_correction_history_atomicity(self):
        obj=self.new()
        with patch('incidents.workflow.IncidentHistory.objects.create',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):review(user=self.users['operador'],pk=obj.pk,action='validar')
        obj.refresh_from_db();self.assertEqual(obj.status,'pendiente')
        review(user=self.users['operador'],pk=obj.pk,action='corregir',public_message='Amplía')
        with patch('incidents.workflow.IncidentHistory.objects.create',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):resubmit(user=self.users['ciudadano'],pk=obj.pk,data={**self.data,'title':'Nuevo título'})
        obj.refresh_from_db();self.assertEqual(obj.title,self.data['title']);self.assertEqual(obj.status,'correccion_solicitada')
    def test_stale_form_cannot_overwrite(self):
        obj=self.valid();old=obj.updated_at.isoformat()
        prioritize(user=self.users['coordinador'],pk=obj.pk,priority='alta',reason='Motivo',expected=old)
        with self.assertRaises(ValidationError):prioritize(user=self.users['coordinador'],pk=obj.pk,priority='baja',reason='Otro motivo',expected=old)
        obj.refresh_from_db();self.assertEqual(obj.priority,'alta')
    def test_priority_and_following_requirements(self):
        obj=self.new()
        with self.assertRaises(ValidationError):prioritize(user=self.users['coordinador'],pk=obj.pk,priority='alta',reason='Motivo')
        obj=self.valid()
        with self.assertRaises(ValidationError):start_following(user=self.users['coordinador'],pk=obj.pk)
        self.task(obj)
        with self.assertRaises(ValidationError):start_following(user=self.users['coordinador'],pk=obj.pk)
        prioritize(user=self.users['coordinador'],pk=obj.pk,priority='alta',reason='Motivo')
        start_following(user=self.users['coordinador'],pk=obj.pk);obj.refresh_from_db();self.assertEqual(obj.status,'en_seguimiento')
    def test_invalid_assignee_and_due_date(self):
        obj=self.valid()
        for role in ('ciudadano','coordinador','administrador'):
            with self.assertRaises(ValidationError):assign_task(user=self.users['coordinador'],incident_id=obj.pk,assignee_id=self.users[role].pk,description='Ejemplo',due_at=timezone.now()+timedelta(days=1))
        with self.assertRaises(ValidationError):assign_task(user=self.users['coordinador'],incident_id=obj.pk,assignee_id=self.users['operador'].pk,description='Ejemplo',due_at=timezone.now()-timedelta(days=1))
        self.assertFalse(Task.objects.exists())
    def test_task_lifecycle_result_and_immutability(self):
        obj,task=self.following()
        with self.assertRaises(ValidationError):act_on_task(user=self.users['operador'],pk=task.pk,action='completar',content='Resultado')
        act_on_task(user=self.users['operador'],pk=task.pk,action='iniciar')
        with self.assertRaises(ValidationError):act_on_task(user=self.users['operador'],pk=task.pk,action='completar',content=' ')
        act_on_task(user=self.users['operador'],pk=task.pk,action='completar',content='Inspección ficticia realizada')
        task.refresh_from_db();self.assertEqual(task.status,'completada');self.assertGreaterEqual(task.finished_at,task.started_at)
        with self.assertRaises(ValidationError):act_on_task(user=self.users['coordinador'],pk=task.pk,action='cancelar',content='Motivo')
    def test_task_requires_following_and_owner(self):
        obj=self.valid();task=self.task(obj)
        with self.assertRaises(ValidationError):act_on_task(user=self.users['operador'],pk=task.pk,action='iniciar')
        with self.assertRaises(Http404):act_on_task(user=self.other_operator,pk=task.pk,action='iniciar')
        self.client.force_login(self.other_operator);self.assertEqual(self.client.post(f'/incidentes/tareas/{task.pk}/iniciar/').status_code,404)
    def test_cancellation_with_reason_and_terminal(self):
        obj=self.valid();task=self.task(obj)
        with self.assertRaises(ValidationError):act_on_task(user=self.users['coordinador'],pk=task.pk,action='cancelar')
        act_on_task(user=self.users['coordinador'],pk=task.pk,action='cancelar',content='Asignación de práctica equivocada')
        task.refresh_from_db();self.assertEqual(task.status,'cancelada')
        self.assertTrue(obj.history.filter(detail__contains='equivocada').exists())
        with self.assertRaises(ValidationError):act_on_task(user=self.users['coordinador'],pk=task.pk,action='cancelar',content='Otra vez')
    def test_task_write_rolls_back_if_history_fails(self):
        obj=self.valid()
        with patch('incidents.workflow.IncidentHistory.objects.create',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):self.task(obj)
        self.assertFalse(Task.objects.exists())
        obj,task=self.following()
        with patch('incidents.workflow.IncidentHistory.objects.create',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):act_on_task(user=self.users['operador'],pk=task.pk,action='iniciar')
        task.refresh_from_db();self.assertEqual(task.status,'pendiente')
    def test_review_queue_and_own_tasks(self):
        pending=self.new();valid=self.valid();task=self.task(valid)
        self.client.force_login(self.users['operador']);r=self.client.get('/incidentes/?bandeja=revision')
        self.assertContains(r,pending.code);self.assertNotContains(r,valid.code)
        self.assertContains(self.client.get('/incidentes/tareas/'),'Inspección ficticia')
        self.client.force_login(self.other_operator);self.assertNotContains(self.client.get('/incidentes/tareas/'),'Inspección ficticia')
    def test_forms_get_readonly_csrf_and_roles(self):
        obj=self.new();self.client.force_login(self.users['operador'])
        self.assertEqual(self.client.get(f'/incidentes/{obj.pk}/revisar/').status_code,200)
        obj.refresh_from_db();self.assertEqual(obj.status,'pendiente')
        c=Client(enforce_csrf_checks=True);c.force_login(self.users['operador'])
        self.assertEqual(c.post(f'/incidentes/{obj.pk}/revisar/',{'action':'validar'}).status_code,403)
        self.client.force_login(self.users['ciudadano']);self.assertEqual(self.client.get(f'/incidentes/{obj.pk}/revisar/').status_code,403)
    def test_post_review_and_coordinator_forms(self):
        obj=self.new();self.client.force_login(self.users['operador'])
        r=self.client.post(f'/incidentes/{obj.pk}/revisar/',{'action':'validar','expected':obj.updated_at.isoformat()})
        self.assertEqual(r.status_code,302);obj.refresh_from_db();self.assertEqual(obj.status,'validado')
        self.client.force_login(self.users['coordinador'])
        for action in ('priorizar','asignar','seguimiento'):self.assertEqual(self.client.get(f'/incidentes/{obj.pk}/{action}/').status_code,200)
    def test_admin_cannot_disable_operator_with_open_tasks(self):
        obj=self.valid();self.task(obj);self.client.force_login(self.users['administrador'])
        user=self.users['operador']
        r=self.client.post(f'/administracion/accounts/user/{user.pk}/change/',{'username':user.username,'email':user.email,'first_name':'Operador','last_name':'Demo','role':'operador','reason':'Intento de desactivación','new_password':''})
        self.assertEqual(r.status_code,200);self.assertContains(r,'tareas abiertas');user.refresh_from_db();self.assertTrue(user.is_active)

class ReviewConcurrencyTests(TransactionTestCase):
    def test_two_reviews_only_one_transition(self):
        users,data=fixtures();obj=create_incident(user=users['ciudadano'],data=data);barrier=Barrier(2)
        def decide(action):
            connections.close_all()
            try:
                user=User.objects.get(pk=users['operador'].pk);barrier.wait(timeout=10)
                try:review(user=user,pk=obj.pk,action=action,reason='Motivo',public_message='Explicación');return 'ok'
                except ValidationError:return 'rechazada'
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(decide,['validar','rechazar']))
        self.assertCountEqual(results,['ok','rechazada']);self.assertEqual(obj.history.count(),2)
