# -*- coding: utf-8 -*-

# Register your models here.
from django.forms import ModelForm
from django.contrib import admin


import logging, traceback, json
logger = logging.getLogger(__name__)


from .models import Customer, Switch, Staff, Recharge, FeatureNumber, InboundGateway

class SwitchAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip_address')

class StaffAdmin(admin.ModelAdmin):
    list_display = ('name', 'skype_id', 'email', 'switch', 'is_admin')

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'skype_group_id', 'switch', 'cfg_asr', 'cfg_enable_sky_net')

class RechargeAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount', 'invoice_id', 'invoice_url', 'is_gateway_confirmed', 'is_expired', 'is_switch_credited', 'is_switch_credit_success', 'created_time')
    list_filter = ('customer',)

class FeatureNumberAdmin(admin.ModelAdmin):
    list_display = ('number', 'country', 'call_model')
    list_filter = ('country', 'call_model')

class InboundGatewayAdmin(admin.ModelAdmin):
    list_display = ('ip', 'customer')
    list_filter = ('customer',)

admin.site.register(Switch, SwitchAdmin)
admin.site.register(Staff, StaffAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Recharge, RechargeAdmin)

admin.site.register(FeatureNumber, FeatureNumberAdmin)
admin.site.register(InboundGateway, InboundGatewayAdmin)


