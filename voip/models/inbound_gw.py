#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from django.db import models
from django.utils import timezone
from django.conf import settings

from common.string_helper import is_not_empty_null
from .switch import Switch
from unipayment import UniPaymentClient, CreateInvoiceRequest

from voip import settings


class InboundGateway(models.Model):
    """
    Feature Number
    """
    ip = models.CharField('IP', max_length=50, default='127.0.0.1')
    customer = models.ForeignKey('Customer', on_delete=models.SET_NULL, null=True)
    description = models.CharField('Description', max_length=1000, default='', blank=True)

    class Meta:
        ordering = ['ip', ]

    def __str__(self):
        return self.ip

    def to_dict(self):
        if self.customer is None:
            return {
                'ip': self.ip,
                'asr': 0.18,
                'enable_sky_net': False,
                'ringtone': False
            }
        else:
            return {
                'ip': self.ip,
                'asr': self.customer.cfg_asr,
                'enable_sky_net': self.customer.cfg_enable_sky_net,
                'ringtone': self.customer.cfg_ringtone
            }