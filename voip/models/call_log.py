#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from django.db import models
from django.utils import timezone
from django.conf import settings


class CallLogManager(models.Manager):
    def upload_call_log(self, country, number, file, gateway):
        self.create(country=country, number=number, file=file, gateway=gateway)

class CallLog(models.Model):
    """
    Call Log
    """
    country = models.CharField(max_length=10, default='86')
    number = models.CharField('Number', max_length=20, default='')
    file = models.CharField(max_length=50, default='', blank=True)
    gateway = models.CharField(max_length=50, default='', blank=True)
    created_time = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_time', ]

    objects = CallLogManager()