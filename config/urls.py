from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from accounts.forms import RoleAuthenticationForm
from accounts.views import home
from config.admin_site import admin_site
from accounts import admin as accounts_admin
from incidents import admin as incidents_admin
from resources import admin as resources_admin
from audit import admin as audit_admin

urlpatterns = [
    path('', home, name='home'),
    path('ingresar/', LoginView.as_view(template_name='registration/login.html', authentication_form=RoleAuthenticationForm), name='login'),
    path('salir/', LogoutView.as_view(), name='logout'),
    path('incidentes/', include('incidents.urls')),
    path('administracion/', admin_site.urls),
]
