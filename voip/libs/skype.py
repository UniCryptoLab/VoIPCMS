#!/usr/bin/python
# -*- coding: utf-8 -*-

from skpy import Skype
from skpy import SkypeEventLoop, SkypeNewMessageEvent

import logging
logger = logging.getLogger(__name__)

from ..models import Staff, Customer, Recharge


class SkypeBot(object):
    def __init__(self, username, password):
        self.sk = Skype(username, password)

    def send_group_message(self, group_id, message):
        channel = self.sk.chats.chat(group_id)
        channel.sendMsg(message)

    def send_contract_message(self, user_id, message):
        ch = self.sk.contacts[user_id].chat
        ch.sendMsg(message)


class SkypeEvent(SkypeEventLoop):

    def __init__(self, username, password):
        logger.info('SkypeEvent inited for user:%s' % username)
        super(SkypeEvent, self).__init__(username, password)
        self.bot = SkypeBot(username, password)

    def onEvent(self, event):
        if isinstance(event, SkypeNewMessageEvent) \
          and not event.msg.userId == self.userId:

            try:
                #print(event.msg)
                skype_id = event.msg.userId
                chat_id = event.msg.chatId
                chat_content = event.msg.content
                is_at_cs = chat_content.startswith('<at id="8:live:.cid.422fc742faec9b8e">CS_3Trunks</at>')
                is_group = chat_id.startswith('19:')

                if is_group:
                    if is_at_cs:
                        args = chat_content[54:].split(' ')
                        cmd = args[0]
                        logger.info('group cmd:%s cmd skype_id:%s chat_id:%s' % (cmd, skype_id, chat_id))
                        cmd_upper = cmd.upper()

                        if cmd_upper in ['HELP', 'H']:
                            self.on_group_help(skype_id, chat_id, args)
                        elif cmd_upper in ['CUSTOMER']:
                            self.on_init_customer(skype_id, chat_id, args)
                        elif cmd_upper in ['NAME', 'N']:
                            self.on_name(skype_id, chat_id, args)
                        elif cmd_upper in ['BALANCE', 'B']:
                            self.on_balance(skype_id, chat_id)
                        elif cmd_upper in ['IP', 'I']:
                            self.on_ip(skype_id, chat_id, args)
                        elif cmd_upper in ['CAPACITY', 'C']:
                            self.on_capacity(skype_id, chat_id, args)
                        elif cmd_upper in ['ROUTE', 'R']:
                            self.on_route(skype_id, chat_id, args)
                        elif cmd_upper == 'DESTORY':
                            self.on_destory_customer(skype_id, chat_id, args)
                        elif cmd_upper in ['PAY', 'P']:
                            self.on_pay(skype_id, chat_id, args)
                        else:
                            logger.info("cmd:%s do not supported" % cmd.upper())
                            self.on_group_help(skype_id, chat_id, args)
                else:
                    staff = Staff.objects.get_staff_by_skype_id(skype_id)
                    if staff is None or not staff.is_admin:
                        logger.info('only staff admin can create customer')
                        self.bot.send_group_message(skype_id, 'please contract with NOC to query data')
                        return
                    args = chat_content[54:].split(' ')
                    cmd = args[0]
                    if cmd.upper() == "REPORT":
                        self.on_report(skype_id, chat_id, args)
            except Exception as e:
                logger.error('process message error:%s' % e)



    def on_group_help(self, skype_id, group_id, args):
        self.bot.send_group_message(group_id, 'Hi team, i am customer service bot, you can type @ me + command to get support.')
        self.bot.send_group_message(group_id, 'Command: balance, pay, ip, capacity, route. (b, p, i, c, r can be recognized too)')

    def on_init_customer(self, skype_id, group_id, args):
        """
        Bind group with account
        :param skype_id:
        :param group_id:
        :param args:
        :return:
        """
        print(args)
        if len(args) < 2:
            self.bot.send_group_message(group_id, 'Hi, please provider customer name.')
            return

        if len(args[1]) < 3:
            self.bot.send_group_message(group_id, 'Hi, customer name should has at least 3 character.')
            return

        staff = Staff.objects.get_staff_by_skype_id(skype_id)
        if staff is None or not staff.is_admin:
            logger.info('only staff admin can create customer')
            self.bot.send_group_message(group_id, 'Please contract with NOC to create customer data')
            return

        if staff.switch is None:
            logger.info('please bind switch to this admin')
            self.bot.send_group_message(group_id, 'Hi, Please contract with NOC to create customer data')
            return

        if not Customer.objects.is_name_valid(args[1]):
            self.bot.send_group_message(group_id, 'Hi team, customer: %s is already created, please check it.' % args[1])
            return

        if not Customer.objects.is_skype_group_id_valid(group_id):
            self.bot.send_group_message(group_id, 'Hi team, we can only handle one customer account in skype group.')
            return

        try:
            ret = staff.switch.init_customer(args[1])
            if ret:
                Customer.objects.init_customer(args[1], group_id, staff, staff.switch)
                self.bot.send_group_message(group_id, 'Hi team, customer account:%s is created' % args[1])
                return
            else:
                staff.switch.destory_customer(args[1])
                self.bot.send_group_message(group_id, 'Hi, Please contract with NOC to create customer data manually')
        except Exception as e:
            staff.switch.destory_customer(args[1])
            Customer.objects.destory_customer(args[1])
            self.bot.send_group_message(group_id, 'Please contract with NOC to create customer data manually')

    def on_name(self, skype_id, group_id, args):
        customer = Customer.objects.get_customer_by_skype_group_id(group_id)
        if customer is None:
            self.bot.send_group_message(group_id,
                                        'Hi team, please create customer account first.')
            return
        self.bot.send_group_message(group_id, 'Hi, this is service group for: %s' % customer.name)

    def on_balance(self, skype_id, group_id):
        customer = Customer.objects.get_customer_by_skype_group_id(group_id)
        if customer is None:
            self.bot.send_group_message(group_id,
                                        'Hi team, please create customer account first.')
            return
        data = customer.switch.get_balance(customer.name)
        if data is not None:
            self.bot.send_group_message(group_id, 'Hi, balance: %s od: %s' % (round(data['balance'], 2), round(data['overdraft'], 2)))
        else:
            self.bot.send_group_message(group_id, 'Hi, please contract with NOC to check balance')

    def on_ip(self, skype_id, group_id, args):
        customer = Customer.objects.get_customer_by_skype_group_id(group_id)
        if customer is None:
            self.bot.send_group_message(group_id,
                                        'Hi team, please create customer account first.')
            return

        if len(args)==1:#query
            data = customer.switch.get_inbound_gateway_info(customer.name)
            print(data)
            if data is not None:
                self.bot.send_group_message(group_id, 'Hi, inbound ip is: %s' % (data['ips']))
            else:
                self.bot.send_group_message(group_id, 'Hi, please contract with NOC to check ip config')
        else:
            staff = Staff.objects.get_staff_by_skype_id(skype_id)
            if staff is None or not staff.is_admin:
                logger.info('only staff admin can set inbound ip')
                self.bot.send_group_message(group_id, 'Hi, please contract with NOC to update ip')
                return
            else:
                staff.switch.update_inbound_gateway_ips(customer.name, args[1])
                data = customer.switch.get_inbound_gateway_info(customer.name)
                if data is not None:
                    self.bot.send_group_message(group_id, 'Hi, current inbound ip is: %s' % (data['ips']))
                else:
                    self.bot.send_group_message(group_id, 'Hi, please contract with NOC to update ip')

    def on_capacity(self, skype_id, group_id, args):
        customer = Customer.objects.get_customer_by_skype_group_id(group_id)
        if customer is None:
            self.bot.send_group_message(group_id,
                                        'Hi team, please create customer account first.')
            return

        if len(args)==1:
            data = customer.switch.get_inbound_gateway_info(customer.name)
            if data is not None:
                self.bot.send_group_message(group_id, 'Hi, capacity is: %s' % (data['ports']))
            else:
                self.bot.send_group_message(group_id, 'Hi, please contract with NOC to check capacity')
        else:
            staff = Staff.objects.get_staff_by_skype_id(skype_id)
            if staff is None or not staff.is_admin:
                logger.info('only staff admin can set inbound capacity')
                self.bot.send_group_message(group_id, 'please contract with NOC to update capacity')
                return
            else:
                staff.switch.update_inbound_gateway_ports(customer.name, args[1])
                data = customer.switch.get_inbound_gateway_info(customer.name)
                if data is not None:
                    self.bot.send_group_message(group_id, 'Hi, current capacity is: %s' % (data['ports']))
                else:
                    self.bot.send_group_message(group_id, 'Hi, please contract with NOC to update capacity')

    def on_route(self, skype_id, group_id, args):
        customer = Customer.objects.get_customer_by_skype_group_id(group_id)
        if customer is None:
            self.bot.send_group_message(group_id,
                                        'Hi team, please create customer account first.')
            return

        if len(args)==1:
            data = customer.switch.get_inbound_gateway_info(customer.name)
            if data is not None:
                self.bot.send_group_message(group_id, 'Hi, route group is: %s' % (data['route_groups']))
            else:
                self.bot.send_group_message(group_id, 'Hi, please contract with NOC to check route group config')
        else:
            staff = Staff.objects.get_staff_by_skype_id(skype_id)
            if staff is None or not staff.is_admin:
                logger.info('only staff admin can set routegroup')
                self.bot.send_group_message(group_id, 'please contract with NOC to update route group')
                return
            else:
                staff.switch.update_inbound_gateway_route_groups(customer.name, args[1])
                data = customer.switch.get_inbound_gateway_info(customer.name)
                if data is not None:
                    self.bot.send_group_message(group_id, 'Hi, current route group is: %s' % (data['route_groups']))
                else:
                    self.bot.send_group_message(group_id, 'Hi, please contract with NOC to update route group')


    def on_pay(self, skype_id, group_id, args):
        customer = Customer.objects.get_customer_by_skype_group_id(group_id)
        if customer is None:
            self.bot.send_group_message(group_id,
                                        'Hi team, please create customer account first.')
            return

        if len(args) < 2:
            self.bot.send_group_message(group_id, 'Hi, please provider amount.')
            return

        if int(args[1]) < 5:
            self.bot.send_group_message(group_id, 'Hi, amount should great than 5.')
            return

        try:
            result = Recharge.objects.add_fund(customer, args[1])
            if result.invoice_id != '':
                self.bot.send_group_message(group_id, 'Hi, please make payment via this url: %s' % result.invoice_url)
                pay_info =  result.get_pay_info()
                if pay_info is not None:
                    self.bot.send_group_message(group_id, 'you can also transfer: %s to %s too.' % (result.amount, pay_info))
            else:
                self.bot.send_group_message(group_id, 'Hi, please contract with support to make payment')
        except Exception as e:
            self.bot.send_group_message(group_id, 'Hi, please contract with support to make payment')



    def on_destory_customer(self, skype_id, group_id, args):
        customer = Customer.objects.get_customer_by_skype_group_id(group_id)
        if customer is None:
            self.bot.send_group_message(group_id,
                                        'Hi team, please create customer account first.')
            return

        staff = Staff.objects.get_staff_by_skype_id(skype_id)
        if staff is None or not staff.is_admin:
            logger.info('only staff admin can destory customer')
            self.bot.send_group_message(group_id, 'Hi, please contract with NOC to close customer account')
            return

        if staff.switch is None:
            logger.info('please bind switch to this admin')
            self.bot.send_group_message(group_id, 'Hi, please contract with NOC to close customer account')
            return

        try:
            staff.switch.destory_customer(customer.name)
            Customer.objects.destory_customer(customer.name)
            self.bot.send_group_message(group_id, 'Hi team, customer account:%s is closed' % customer.name)
        except Exception as e:
            logger.error('destory customer error:%s' % e)
            self.bot.send_group_message(group_id, 'Hi, please contract with NOC to close customer manually')


    def on_report(self, skype_id, chat_id, args):
        self.bot.send_contract_message(skype_id, 'report data')

