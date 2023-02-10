#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from django.db import models


class OutboundGateway(models.Model):
    """
    Outbound Gateway
    """
    name = models.CharField('Name', max_length=50, default='Gateway')
    ip = models.CharField('IP', max_length=50, default='127.0.0.1')
    description = models.CharField('Description', max_length=1000, default='', blank=True)

    class Meta:
        ordering = ['name', ]

    def __str__(self):
        return self.ip