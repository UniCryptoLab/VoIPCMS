#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
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
    skype_group_id = models.CharField('SkypeGroupId', max_length=100, default='', blank=True, null=True)
    prefix = models.CharField('Prefix', max_length=10, default='', blank=True, null=True)
    creator = models.ForeignKey(Staff, verbose_name='Creator', related_name='customers',  on_delete=models.SET_NULL, null=True)
    staff = models.ForeignKey(Staff, verbose_name='Sales', related_name='sale_customers', on_delete=models.SET_NULL, null=True)
    switch = models.ForeignKey('Switch', verbose_name='Switch', on_delete=models.SET_NULL, null=True)
    email = models.EmailField('Email', max_length=100, default='user@example.com')
    website = models.URLField('Website', max_length=100, default='https://example.com')
    cfg_asr = models.FloatField('ASR', default=0.18)
    cfg_silent = models.FloatField('Silent', default=0)
    cfg_ringtone = models.BooleanField(default=False, verbose_name='RingTone')
    cfg_peak_close_trunk = models.BooleanField(default=True, verbose_name='Peak Close Trunk')
    cfg_carrier_ivr = models.BooleanField(default=True, verbose_name='Carrier IVR')
    cfg_enable_sky_net = models.BooleanField(default=False, verbose_name='SkyNet')
    cfg_mix_ratio = models.FloatField('MixRatio', default=0)
    description = models.CharField('Description', max_length=1000, default='', blank=True)

    objects = CustomerManager()

    class Meta:
        ordering = ['prefix', ]

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
                'prefix': self.prefix,
                'asr': self.cfg_asr,
                'silent': self.cfg_silent,
                'enable_sky_net': self.cfg_enable_sky_net,
                'peak_close_trunk': self.cfg_peak_close_trunk,
                'carrier_ivr': self.cfg_carrier_ivr,
                'ringtone': self.cfg_ringtone,
                'mix_ratio': self.cfg_mix_ratio,#when sky net enable, mix_ratio is used for trunk / local
                'name': self.name
            }


@receiver(post_save, sender=Customer)
def update_customer_prefix(sender, instance, created, **kwargs):
    if created:
        instance.prefix = ('%s' % instance.pk).zfill(3)
        instance.save()
    else:
        if instance.prefix == '':
            instance.prefix = ('%s' % instance.pk).zfill(3)
            instance.save()






