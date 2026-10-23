from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from accounts.roles import roles_required, role_of
from .forms import IncidentForm
from .services import create_incident, visible_incidents

@roles_required('ciudadano', 'operador', 'coordinador')
def incident_list(request):
    qs = visible_incidents(request.user)
    return render(request, 'incidents/list.html', {'page_obj': Paginator(qs, 10).get_page(request.GET.get('page')), 'total': qs.count()})

@roles_required('ciudadano', 'operador', 'coordinador')
def incident_detail(request, pk):
    obj = get_object_or_404(visible_incidents(request.user), pk=pk)
    history = obj.history.all()
    if role_of(request.user) == 'ciudadano':
        history = history.exclude(citizen_message__isnull=True).exclude(citizen_message='')
    return render(request, 'incidents/detail.html', {'incident': obj, 'history': history})

@roles_required('ciudadano')
@require_http_methods(['GET', 'POST'])
def incident_create(request):
    form = IncidentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            obj = create_incident(user=request.user, data=form.cleaned_data)
        except ValidationError as exc:
            for error in exc.messages: form.add_error(None, error)
        else:
            messages.success(request, 'Reporte registrado. Puedes consultar su estado en esta ficha.')
            return redirect('incidents:detail', pk=obj.pk)
    return render(request, 'incidents/form.html', {'form': form})
