#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from django.db import models
from .staff import Staff


class CustomerManager(models.Manager):
    def is_name_valid(self, name):
        return not self.filter(name=name).count()>0

    def is_skype_group_id_valid(self, skype_group_id):
        return not self.filter(skype_group_id=skype_group_id).count()>0

    def get_customer_by_skype_group_id(self, skype_group_id):
        try:
            return self.get(skype_group_id=skype_group_id)
        except Customer.DoesNotExist as e:
            return None

    def init_customer(self, name, skype_group_id, creator, switch):
        self.create(name=name,skype_group_id=skype_group_id, creator=creator, switch=switch)

    def destory_customer(self,name):
        for customer in self.filter(name=name).all():
            customer.delete()



class Customer(models.Model):
    """
    Customer
    """
    name = models.CharField('Name', max_length=50, default='name')
    skype_group_id = models.CharField('SkypeGroupId', max_length=200, default='', blank=True, null=True)
    creator = models.ForeignKey(Staff, verbose_name='Creator', related_name='customers',  on_delete=models.SET_NULL, null=True)
    staff = models.ForeignKey(Staff, verbose_name='Sales', related_name='sale_customers', on_delete=models.SET_NULL, null=True)
    switch = models.ForeignKey('Switch', verbose_name='Switch', on_delete=models.SET_NULL, null=True)
    cfg_asr = models.FloatField('ASR', default=0.18)
    cfg_enable_sky_net = models.BooleanField(default=False, verbose_name='SkyNet')
    description = models.CharField('Description', max_length=1000, default='', blank=True)

    objects = CustomerManager()

    class Meta:
        ordering = ['name', ]

    def __str__(self):
        return self.name




