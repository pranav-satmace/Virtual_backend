# Register your models here.
from django.contrib import admin
from .models import UserProfile

from .models import ReportingTenant, Tenant, Entity,Center, Warehouse
from .models import TradePartner, TradePartnerAddress, TradePartnerBankAccount, GoodsReceiptNote, GrnLineItem

admin.site.register(Tenant)
admin.site.register(ReportingTenant)
admin.site.register(UserProfile)
admin.site.register(Warehouse)
admin.site.register(TradePartner)
admin.site.register(TradePartnerAddress)
admin.site.register(TradePartnerBankAccount)
# admin.site.register(Address)
# admin.site.register(Currency)
admin.site.register(GoodsReceiptNote)
admin.site.register(GrnLineItem)
admin.site.register(Entity)
admin.site.register(Center)
