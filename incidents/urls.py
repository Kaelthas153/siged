from django.urls import path
from . import views
app_name = 'incidents'
urlpatterns = [path('', views.incident_list, name='list'), path('nuevo/', views.incident_create, name='create'), path('<int:pk>/', views.incident_detail, name='detail')]
