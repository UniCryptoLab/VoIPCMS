# -*- coding: utf-8 -*-

# Register your models here.
from django.forms import ModelForm
from django.urls import path
from django.contrib import admin, messages
from django.urls import reverse
from django.http import HttpResponse, HttpResponseNotFound, Http404 ,HttpResponseRedirect, JsonResponse
from django.utils.html import format_html

import logging, traceback, json
logger = logging.getLogger(__name__)


from .models import Customer, Switch, Staff, Recharge, FeatureNumber, InboundGateway, CallLog, ErrorFile

class SwitchAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip_address')

class StaffAdmin(admin.ModelAdmin):
    list_display = ('name', 'skype_id', 'email', 'switch', 'is_admin')

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'skype_group_id', 'switch', 'prefix', 'cfg_asr', 'cfg_ringtone', 'cfg_enable_sky_net', 'cfg_mix_ratio')
    list_filter = ('switch',)
    fieldsets = (
        (None, {
            "fields": [
                "name", "email", "website",
            ]
        }),
        ("Config", {
            "fields": [
                "cfg_asr", "cfg_ringtone", "cfg_enable_sky_net", "cfg_mix_ratio"
            ]
        }),
        ("Biz", {
            "fields": [
                "prefix", "switch"
            ]
        }),

        ("Other", {

            "fields": [
                "creator", "staff", "skype_group_id", "description"
            ]
        })
    )

    def get_readonly_fields(self, request, obj=None):
        return ['prefix']

    def customer_action(self, obj):
        """

        """
        return format_html(
            '<a href="{}" target="_blank">Inbound</a>&nbsp;'
            '| <a href="{}" >Framework</a>&nbsp;',
            reverse('admin:customer-sync-inbound', args=[obj.pk]),
            reverse('admin:customer-demo', args=[obj.pk]),
        )

    customer_action.allow_tags = True
    customer_action.short_description = "Action"

    def get_urls(self):
        # use get_urls for easy adding of views to the admin
        urls = super(CustomerAdmin, self).get_urls()
        my_urls = [
            #path(
            #    r'^(?P<customer_id>.+)/sync_inbound_gateway/$',
            #    self.admin_site.admin_view(self.upload_permission),
            #    name='deploy-upload-permission',
            #),
        ]

        return my_urls + urls

    def sync_inbound_gateway(self, request, customer_id):
        previous_url = request.META.get('HTTP_REFERER')
        customer = Customer.objects.get(id=customer_id)
        if customer.switch is not None:
            gws = customer.switch.get_inbound_gateway_info(customer.name)

        #for ip in gws.split(','):


        messages.info(request, "Send Permission Update Success")
        return HttpResponseRedirect(previous_url)


class RechargeAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount', 'invoice_id', 'invoice_url', 'is_gateway_confirmed', 'is_expired', 'is_switch_credited', 'is_switch_credit_success', 'created_time')
    list_filter = ('customer',)

class FeatureNumberAdmin(admin.ModelAdmin):
    list_display = ('number', 'country', 'call_model', 'created_time')
    list_filter = ('country', 'call_model')
    search_fields = ('number',)

class InboundGatewayAdmin(admin.ModelAdmin):
    list_display = ('ip', 'customer')
    list_filter = ('customer',)

class CallLogAdmin(admin.ModelAdmin):
    list_display = ('prefix', 'number', 'file', 'gateway', 'created_time')
    list_filter = ('gateway', 'prefix')
    search_fields = ('number',)

class ErrorFileAdmin(admin.ModelAdmin):
    list_display = ('country', 'file', 'created_time')
    list_filter = ('country', )
    search_fields = ('file',)

admin.site.register(Switch, SwitchAdmin)
admin.site.register(Staff, StaffAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Recharge, RechargeAdmin)

admin.site.register(FeatureNumber, FeatureNumberAdmin)
admin.site.register(CallLog, CallLogAdmin)
admin.site.register(ErrorFile, ErrorFileAdmin)
#admin.site.register(InboundGateway, InboundGatewayAdmin)


