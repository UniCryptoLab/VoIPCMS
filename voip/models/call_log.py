#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from django.db import models
from django.utils import timezone
from django.conf import settings


class CallLogManager(models.Manager):
    def upload_call_log(self, prefix, number, file, gateway):
        if prefix is None or file is None or gateway is None:
            return 
        self.create(prefix=prefix, number=number, file=file, gateway=gateway)

class CallLog(models.Model):
    """
    Call Log
    """
    prefix = models.CharField(max_length=10, default='001')
    number = models.CharField(max_length=20, default='')
    file = models.CharField(max_length=50, default='', blank=True)
    gateway = models.CharField(max_length=50, default='', blank=True)
    created_time = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_time', ]

    objects = CallLogManager()