#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from django.db import models
from ..libs.vos import VOSAPI

class Switch(models.Model):
    """
    Switch
    """
    name = models.CharField('Name', max_length=50, default='name')
    ip_address = models.CharField('IP', max_length=50, default='name')
    api_url = models.CharField('API Url', max_length=200, default='')
    description = models.CharField('Description', max_length=1000, default='', blank=True)

    class Meta:
        ordering = ['name', ]

    def __str__(self):
        return self.name

    def init_customer(self, name):
        vos = VOSAPI(self.api_url)
        ret = vos.init_customer(name)
        return ret

    def get_balance(self, name):
        vos = VOSAPI(self.api_url)
        return vos.get_balance(name)

    def get_inbound_gateway_info(self, name):
        vos = VOSAPI(self.api_url)
        return vos.get_inbound_gateway_info(name)

    def update_inbound_gateway_ips(self, name, ips):
        vos = VOSAPI(self.api_url)
        vos.update_ips(name, ips)

    def update_inbound_gateway_ports(self, name, ports):
        vos = VOSAPI(self.api_url)
        vos.update_ports(name, ports)

    def update_inbound_gateway_route_groups(self, name, route_groups):
        vos = VOSAPI(self.api_url)
        vos.update_route_groups(name, route_groups)

    def credit_customer(self, name, amount, ref):
        vos = VOSAPI(self.api_url)
        return vos.credit_customer(name, amount, ref)

    def destory_customer(self,name):
        vos = VOSAPI(self.api_url)
        vos.destory_customer(name)


