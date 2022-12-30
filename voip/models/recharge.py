#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from django.db import models
from django.utils import timezone
from django.conf import settings

from .switch import Switch
from unipayment import UniPaymentClient, CreateInvoiceRequest

from voip import settings


class RechargeManager(models.Manager):
    def add_fund(self, customer, amount):
        recharge = self.create(customer=customer, customer_name=customer.name, amount=amount)

        client = UniPaymentClient(settings.UNIPAYMENT_CLIENT_ID, settings.UNIPAYMENT_CLIENT_SECRET)
        request = CreateInvoiceRequest()
        request.app_id = settings.UNIPAYMENT_APP_ID
        request.price_amount = amount
        request.price_currency = 'USD'
        request.pay_currency = 'USDT'
        request.network = 'NETWORK_TRX'
        request.notify_url = 'https://%s/voip/payment/notify' % settings.CMS_HOST
        request.redirect_url = 'https://%s/recharge' % settings.CMS_HOST
        request.order_id = recharge.pk
        request.title = 'Recharge Account'
        request.description = 'Recharge Account: %s %s$' % (customer.name, amount)
        create_invoice_response = client.create_invoice(request)

        if create_invoice_response.code == 'OK':
            recharge.invoice_id = create_invoice_response.data.invoice_id
            recharge.invoice_url = create_invoice_response.data.invoice_url
            recharge.save()
        else:
            recharge.invoice_create_error = create_invoice_response.msg
            recharge.save()

        return recharge

    def get_recharge_by_invoice_id(self,invoice_id):
        try:
            return self.get(invoice_id=invoice_id)
        except Recharge.DoesNotExist as e:
            return None

    def get_recharge_to_credit(self):
        return self.filter(is_gateway_confirmed=True).filter(is_switch_credited=False).all()


class Recharge(models.Model):
    """
    Recharge
    """
    customer = models.ForeignKey('Customer', verbose_name='Customer', on_delete=models.SET_NULL, null=True)
    customer_name = models.CharField('CustomerName', max_length=50, default='', blank=True) #keep name stored if customer is destoried
    amount = models.DecimalField('Amount', decimal_places=2, max_digits=8, default=0)

    invoice_id = models.CharField('InvoiceId', max_length=50, default='', blank=True)
    invoice_url = models.CharField('InvoiceUrl', max_length=50, default='', blank=True)

    is_gateway_confirmed = models.BooleanField('GatewayConfirm', default=False)
    gateway_confirmed_time = models.DateTimeField(default=None, null=True, blank=True)

    is_expired = models.BooleanField('IsExpired', default=False)
    expired_time = models.DateTimeField(default=None, null=True, blank=True)

    is_switch_credited = models.BooleanField('SwitchCredit', default=False)
    switch_credited_time = models.DateTimeField(default=None, null=True, blank=True)
    is_switch_credit_success = models.BooleanField('SwitchCredit', default=False)
    credit_mark = models.CharField('CreditMark', max_length=128, default='', blank=True)


    invoice_create_error = models.CharField('Invoice Create Error', max_length=200, default='', blank=True)
    created_time = models.DateTimeField(default=timezone.now)

    mark = models.CharField('Mark', max_length=1000, default='', blank=True)

    objects = RechargeManager()

    class Meta:
        ordering = ['pk', ]


    def __str__(self):
        return 'Order:%s' % self.pk