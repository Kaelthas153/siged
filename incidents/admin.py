from django.contrib import admin
from config.admin_site import admin_site
from audit.admin import AuditedAdmin
from .models import Zone, ThreatType

@admin.register(Zone, site=admin_site)
class ZoneAdmin(AuditedAdmin):
    list_display = ('code', 'name', 'municipality', 'active')
    list_filter = ('active',)

@admin.register(ThreatType, site=admin_site)
class ThreatTypeAdmin(AuditedAdmin):
    list_display = ('name', 'active')
