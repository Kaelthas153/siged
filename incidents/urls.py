from django.urls import path
from . import views
from . import workflow_views
app_name = 'incidents'
urlpatterns = [path('', views.incident_list, name='list'), path('nuevo/', views.incident_create, name='create'),
    path('tareas/',workflow_views.task_list,name='tasks'),
    path('tareas/<int:pk>/<str:action>/',workflow_views.task_action,name='task_action'),
    path('<int:pk>/', views.incident_detail, name='detail'),
    path('<int:pk>/<str:action>/',workflow_views.incident_action,name='action')]
