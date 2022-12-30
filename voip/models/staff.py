#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from django.db import models
from .switch import Switch


class StaffManager(models.Manager):
    def get_staff_by_skype_id(self, skype_id):
        try:
            return self.get(skype_id=skype_id)
        except Staff.DoesNotExist:
            return None

class Staff(models.Model):
    """
    Staff
    """
    name = models.CharField('Name', max_length=50, default='name')
    skype_id = models.CharField('SkypeId', max_length=200, default='')
    email = models.EmailField('Email', max_length=50, default='sales@example.com')
    switch = models.ForeignKey(Switch, verbose_name='Switch', on_delete=models.SET_NULL, null=True)
    is_admin = models.BooleanField('IsAdmin', default=False)
    description = models.CharField('Description', max_length=1000, default='', blank=True)

    objects = StaffManager()
    class Meta:
        ordering = ['name', ]

    def __str__(self):
        return self.name