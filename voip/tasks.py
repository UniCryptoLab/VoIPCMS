#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.utils import timezone
from .models import Recharge, Customer
import logging
logger = logging.getLogger(__name__)


from voip.libs.skype import SkypeBot
from voip import settings
skype_bot = SkypeBot(settings.SKYPE_USERNAME, settings.SKYPE_PASS)


@shared_task
def demo_task():
    logger.info('log task information')
    for customer in Customer.objects.all():
        if customer.switch is not None:
            data = customer.switch.get_balance(customer.name)
            skype_bot.send_group_message(customer.skype_group_id, 'Hi, balance:%s od:%s' % (data['balance'], data['overdraft']))


@shared_task
def notify_balance():
    for customer in Customer.objects.all():
        if customer.switch is not None:
            data = customer.switch.get_balance(customer.name)
            skype_bot.send_group_message(customer.skype_group_id, 'Hi, balance:%s od:%s' % (data['balance'], data['overdraft']))


@shared_task
def recharge_handler():
    logger.info('process pending recharges')

    # handle recharge to credit
    recharges = Recharge.objects.get_recharge_to_credit()
    for item in recharges:
        if item.customer is not None:
            if item.customer.switch is not None:
                ret = item.customer.switch.credit_customer(item.customer.name, float(item.amount), item.invoice_id)
                item.is_switch_credited = True
                if not ret:
                    item.is_switch_credit_success = False
                    item.credit_mark = 'credit failed'
                else:
                    item.is_switch_credit_success = True
                    item.switch_credited_time = timezone.now()
            else:
                item.credit_mark = 'Customer has no switch'
        else:
            item.credit_mark = 'Customer field of recharge is None'

        item.save()

        try:
            if item.is_switch_credit_success:
                data = item.customer.switch.get_balance(item.customer.name)
                msg = 'Hi, topup %s$ to account success, current balance:%s' % (item.amount, data['balance'])
            else:
                msg = 'Hi, topup %s$ to account fail, reason:%s, please contract NOC' % (item.amount, item.credit_mark)
            skype_bot.send_group_message(item.customer.skype_group_id, msg)
        except Exception as e:
            logger.error('send notification error')


    # handle expired recharge to notify
    for item in Recharge.objects.get_expired_recharge_to_notify():
        if item.customer is not None:
            item.is_expired_notified = True
            item.save()
            msg = 'Hi, recharge: #%s is expired, please generate new one.' % item.pk
            skype_bot.send_group_message(item.customer.skype_group_id, msg)





