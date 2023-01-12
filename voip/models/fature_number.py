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


CALL_MODEL = (
    ('Direct', 'Direct'),
    ('Bypass', 'Bypass'),
    ('Auto', 'Auto'),
    ('Block', 'Block'),
)

COUNTRY = (
    ('86', '86'),
    ('852', '852'),
)


class FeatureNumber(models.Model):
    """
    Feature Number
    """
    number = models.CharField('Number', max_length=50, default='')
    call_model = models.CharField(max_length=10, choices=CALL_MODEL, default='Auto')
    country = models.CharField(max_length=10, choices=COUNTRY, default='86')
    description = models.CharField('Description', max_length=1000, default='', blank=True)

    class Meta:
        ordering = ['number', ]

    def __str__(self):
        return self.number


    def to_dict(self):
        return {
            'number': self.number,
            'call_model': self.call_model,
            'country': self.country
        }