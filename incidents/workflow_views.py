from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from accounts.roles import roles_required, role_of
from tasks.models import Task
from tasks.services import assign_task, act_on_task
from .services import visible_incidents
from .workflow import review, resubmit, prioritize, start_following
from .workflow_forms import ReviewForm, CorrectionForm, PriorityForm, AssignmentForm, VersionForm, TaskActionForm

ACTION_FORMS = {
    'revisar': ('operador', ReviewForm, 'Revisar información', 'Guardar decisión'),
    'corregir': ('ciudadano', CorrectionForm, 'Corregir y reenviar', 'Guardar corrección y reenviar'),
    'priorizar': ('coordinador', PriorityForm, 'Definir prioridad', 'Guardar prioridad'),
    'asignar': ('coordinador', AssignmentForm, 'Asignar una tarea', 'Crear tarea'),
    'seguimiento': ('coordinador', VersionForm, 'Iniciar seguimiento', 'Confirmar inicio de seguimiento'),
}

@roles_required('ciudadano','operador','coordinador')
@require_http_methods(['GET','POST'])
def incident_action(request, pk, action):
    if action not in ACTION_FORMS: raise Http404
    role, form_class, title, submit = ACTION_FORMS[action]
    from accounts.roles import require_role
    require_role(request.user,role)
    obj = get_object_or_404(visible_incidents(request.user),pk=pk)
    initial={'expected':obj.updated_at.isoformat()}
    if action=='corregir':
        initial.update({field:getattr(obj,field) for field in ('title','description','location_reference','occurred_at')})
        initial.update(zone=obj.zone_id,threat_type=obj.threat_type_id)
    if action=='priorizar': initial['priority']=obj.priority
    form=form_class(request.POST if request.method=='POST' else None,initial=initial)
    allowed={'revisar':obj.status in ('pendiente','reenviado'),'corregir':obj.status=='correccion_solicitada',
             'priorizar':obj.status in ('validado','en_seguimiento'),'asignar':obj.status in ('validado','en_seguimiento'),
             'seguimiento':obj.status=='validado'}[action]
    if not allowed:
        messages.error(request,'Esta acción ya no está disponible en el estado actual.')
        return redirect('incidents:detail',pk=pk)
    if request.method=='POST' and form.is_valid():
        data=form.cleaned_data
        try:
            if action=='revisar': review(user=request.user,pk=pk,**data)
            elif action=='corregir': resubmit(user=request.user,pk=pk,data=data,expected=data['expected'])
            elif action=='priorizar': prioritize(user=request.user,pk=pk,**data)
            elif action=='asignar': assign_task(user=request.user,incident_id=pk,assignee_id=data['assignee'].pk,description=data['description'],due_at=data['due_at'],expected=data['expected'])
            else: start_following(user=request.user,pk=pk,expected=data['expected'])
        except ValidationError as exc:
            for message in exc.messages:form.add_error(None,message)
        else:
            messages.success(request,'Acción guardada y añadida al historial.')
            return redirect('incidents:detail',pk=pk)
    observation=obj.history.filter(action='corregir').order_by('-created_at','-pk').first() if action=='corregir' else None
    return render(request,'incidents/action.html',{'form':form,'incident':obj,'title':title,'submit':submit,'observation':observation})

@roles_required('operador','coordinador')
def task_list(request):
    qs=Task.objects.select_related('incident','assignee').filter(status__in=['pendiente','en_progreso']).order_by('due_at','pk')
    if role_of(request.user)=='operador': qs=qs.filter(assignee=request.user)
    return render(request,'tasks/list.html',{'page_obj':Paginator(qs,10).get_page(request.GET.get('page')),'total':qs.count()})

@roles_required('operador','coordinador')
@require_http_methods(['GET','POST'])
def task_action(request,pk,action):
    from accounts.roles import require_role
    if action not in ('iniciar','completar','cancelar'):raise Http404
    require_role(request.user,'coordinador' if action=='cancelar' else 'operador')
    qs=Task.objects.select_related('incident','assignee')
    if role_of(request.user)=='operador':qs=qs.filter(assignee=request.user)
    task=get_object_or_404(qs,pk=pk)
    form=TaskActionForm(request.POST if request.method=='POST' else None)
    if action=='iniciar':form.fields.pop('content')
    else:
        form.fields['content'].required=True
        form.fields['content'].label='Resultado de la tarea' if action=='completar' else 'Motivo de cancelación'
    if request.method=='POST' and form.is_valid():
        try: act_on_task(user=request.user,pk=pk,action=action,content=form.cleaned_data.get('content',''))
        except ValidationError as exc:
            for message in exc.messages:form.add_error(None,message)
        else:
            messages.success(request,'Tarea actualizada con historial.')
            return redirect('incidents:detail',pk=task.incident_id)
    return render(request,'incidents/action.html',{'form':form,'incident':task.incident,'task':task,'title':action.capitalize()+' tarea','submit':'Confirmar '+action})
