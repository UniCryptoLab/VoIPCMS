#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.db import models


class IP(models.Model):
    """
    IP in black list
    """
    name = models.CharField('Name', max_length=100, default='Node')
    ip = models.CharField('IP', max_length=50, default='127.0.0.1')
    is_blocked = models.BooleanField('Blocked', default=False)
