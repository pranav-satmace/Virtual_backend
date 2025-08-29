# Register your models here.
from django.contrib import admin
from .models import UserProfile

from .models import ReportingTenant
from .models import Tenant
from .models import Entity
from .models import Center
from .models import Warehouse

admin.site.register(UserProfile)
admin.site.register(Tenant)
admin.site.register(ReportingTenant)
admin.site.register(Warehouse)
# admin.site.register(Address)
# admin.site.register(Currency)
admin.site.register(Entity)
admin.site.register(Center)
