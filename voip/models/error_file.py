#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from django.db import models
from django.utils import timezone
from django.conf import settings


class ErrorFile(models.Model):
    """
    Error File
    """
    country = models.CharField(max_length=10, default='86')
    file = models.CharField(max_length=100, default='', blank=True, unique=True)
    created_time = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_time', ]

    @property
    def file_url(self):
        return 'http://file.3trunks.net:8080/ivr/%s' % self.file

    def save(self, *args, **kwargs):
        self.file = self.file.strip()
        super().save(*args, **kwargs)
