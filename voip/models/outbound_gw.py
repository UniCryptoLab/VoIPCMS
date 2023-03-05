#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from django.db import models
from django.utils import timezone

class OutboundGateway(models.Model):
    """
    Outbound Gateway
    """
    name = models.CharField('Name', max_length=50, default='Gateway')
    ip = models.CharField('IP', max_length=50, default='127.0.0.1')
    internal_ip = models.CharField('Internal IP', max_length=50, default='127.0.0.1')

    description = models.CharField('Description', max_length=1000, default='', blank=True)

    last_heartbeat = models.DateTimeField('Heartbeat', default=timezone.now, blank=True)

    uptime = models.IntegerField('Uptime', default=0, blank=True)

    cpu_model = models.CharField('CPU', max_length=100, default='', blank=True)
    cpu_cnt = models.IntegerField('CPU Count', default=0)
    cpu_used_percent = models.FloatField('CPU Used Percent', default=0)

    memory_total = models.BigIntegerField('Memory Total', default=0)
    memory_used = models.BigIntegerField('Memory Used', default=0)

    disk_total = models.BigIntegerField('Disk Total', default=0)
    disk_used = models.BigIntegerField('Disk Used', default=0)

    asterisk_current_calls = models.BigIntegerField('Current Calls', default=0)
    asterisk_status = models.CharField('Gateway Status', max_length=20, default='', blank=True)

    alert_enable = models.BooleanField('Enable Alert', default=True)

    class Meta:
        ordering = ['name', ]

    def _update_heartbeat(self, need_save=True):
        self.last_heartbeat = timezone.now()
        if need_save:
            self.save()

    def _is_online(self):
        """
        if server do not receive info in 3 minutes, we think it is gone
        :return:
        """
        now = timezone.now()
        if (now - self.last_heartbeat).total_seconds() > 60*3:
            return False
        return True

    _is_online.boolean = True
    _is_online.short_description = 'Online'
    is_online = property(_is_online)

    def up_time(self):
        if self.uptime < 3600:
            return '%sm' % round(self.uptime/60, 2)
        else:
            return '%sh' % round(self.uptime/3600, 2)

    def gateway_info(self):
        return '%s - %s' % (self.asterisk_current_calls, self.asterisk_status)

    gateway_info.short_description = 'Gateway Info'

    def statistic(self):
        cpu_percent = 'Na'
        memory_percent ='Na'
        disk_percent = 'Na'

        cpu_percent = self.cpu_used_percent
        if self.memory_total >0:
            memory_percent = round(self.memory_used * 100 / self.memory_total, 2)
        if self.disk_total >0:
            disk_percent = round(self.disk_used * 100/ self.disk_total, 2)

        return '%s - %s - %s' % (cpu_percent, memory_percent, disk_percent)

    def update_local_info(self, data):
        if 'uptime' in data:
            self.uptime = data['uptime']

        if 'internal_ip' in data:
            self.internal_ip = data['internal_ip']

        if 'cpu' in data:
            self.cpu_model = data['cpu']['brand']
            self.cpu_cnt = data['cpu']['count']
            self.cpu_used_percent = data['cpu']['used_percent']

        if 'memory' in data:
            self.memory_total = data['memory']['total']
            self.memory_used = data['memory']['used']

        if 'disk' in data:
            self.disk_total = data['disk']['total']
            self.disk_used = data['disk']['used']

        if 'asterisk' in data:
            self.asterisk_current_calls = data['asterisk']['calls']
            self.asterisk_status = data['asterisk']['status']


        self._update_heartbeat()
        self.save()


    def __str__(self):
        return self.ip