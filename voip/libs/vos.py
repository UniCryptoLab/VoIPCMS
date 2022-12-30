#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import requests

logger = logging.getLogger(__name__)


class VOSAPI(object):
    def __init__(self, url):
        self.base_url = url

    def init_customer(self, name):
        ret, rate = self.create_rate_group(name)
        if not ret:
            return False
        ret, cust = self.create_customer(name, name)
        if not ret:
            return False
        ret, gw = self.create_inbound_gateway(name)
        if not ret:
            return False
        return True

    def destory_customer(self, name):
        self.delete_inbound_gateway(name)
        self.delete_customer(name)
        self.delete_rate_group(name)


    def get_customer(self, name):
        url = '%s/external/server/GetCustomer' % self.base_url
        resp = requests.post(url=url, verify=False, json={'accounts': [name]})
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                if len(data['infoCustomers']) > 0:
                    return data['infoCustomers'][0]
        return None

    def delete_customer(self, name):
        url = '%s/external/server/DeleteCustomer' % self.base_url
        resp = requests.post(url=url, verify=False, json={'account': name})
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                return True
        return False

    def create_customer(self, name, rate=''):
        url = '%s/external/server/CreateCustomer' % self.base_url
        req = {'account': name}
        if rate != '':
            if self.get_rate_group(rate) is not None:
                req = {'account': name, 'feeRateGroup': name}
        resp = requests.post(url=url, verify=False, json=req)
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                return (True, self.get_customer(name))
            return (False, None)
        return (False, None)


    def get_rate_group(self, name):
        url = '%s/external/server/GetFeeRateGroup' % self.base_url
        resp = requests.post(url=url, verify=False, json={'names': [name]})
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                if len(data['infoFeeRateGroups']) > 0:
                    return data['infoFeeRateGroups'][0]
        return None

    def delete_rate_group(self, name):
        url = '%s/external/server/DeleteFeeRateGroup' % self.base_url
        resp = requests.post(url=url, verify=False, json={'name': name})
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                return True
            elif data['retCode'] == '-10007':
                #Not found, operation failed
                return False
        return False


    def create_rate_group(self, name):
        url = '%s/external/server/CreateFeeRateGroup' % self.base_url
        resp = requests.post(url=url, verify=False, json={'name': name})
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                return (True, self.get_rate_group(name))
            return (False, None)
        return (False, None)


    def get_inbound_gateway(self, name):
        url = '%s/external/server/GetGatewayMapping' % self.base_url
        resp = requests.post(url=url, verify=False, json={'names': [name]})
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                if len(data['infoGatewayMappings']) > 0:
                    return data['infoGatewayMappings'][0]
        return None

    def create_inbound_gateway(self, name):
        url = '%s/external/server/CreateGatewayMapping' % self.base_url
        resp = requests.post(url=url, verify=False, json={'name': name, 'callLevel':5, 'account': name, 'registerType':0})
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                return (True, self.get_rate_group(name))
            return (False, None)
        return (False, None)

    def update_ips(self, name, ips):
        gw = self.get_inbound_gateway(name)
        if gw is None:
            return False
        #print(gw)
        url = '%s/external/server/ModifyGatewayMapping' % self.base_url
        gw['remoteIps']=ips
        resp = requests.post(url=url, verify=False, json=gw)
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                return True
            return False
        return False

    def update_route_group(self,name, route_groups):
        gw = self.get_inbound_gateway(name)
        if gw is None:
            return False
        # print(gw)
        url = '%s/external/server/ModifyGatewayMapping' % self.base_url
        gw['routingGatewayGroups'] = route_groups
        resp = requests.post(url=url, verify=False, json=gw)
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                return True
            return False
        return False

    def update_ports(self,name, ports):
        gw = self.get_inbound_gateway(name)
        if gw is None:
            return False
        # print(gw)
        url = '%s/external/server/ModifyGatewayMapping' % self.base_url
        gw['capacity'] = ports
        resp = requests.post(url=url, verify=False, json=gw)
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                return True
            return False
        return False

    def update_route_groups(self,name, route_groups):
        gw = self.get_inbound_gateway(name)
        if gw is None:
            return False
        # print(gw)
        url = '%s/external/server/ModifyGatewayMapping' % self.base_url
        gw['routingGatewayGroups'] = route_groups
        resp = requests.post(url=url, verify=False, json=gw)
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                return True
            return False
        return False


    def delete_inbound_gateway(self, name):
        url = '%s/external/server/DeleteGatewayMapping' % self.base_url
        resp = requests.post(url=url, verify=False, json={'name': name})
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                return True
        return False

    def credit_customer(self, name, amount, ref):
        """
        topup customer
        :param name:
        :param amount:
        :param ref:
        :return:
        """
        url = '%s/external/server/Pay' % self.base_url
        resp = requests.post(url=url, verify=False, json={'ownerName': name, 'ownerType':2, 'money': amount, 'memo': ref})
        if resp.status_code == 200:
            data = resp.json()
            logger.debug('result:%s' % data)
            if data['retCode'] == 0:
                return True
        return False

    def get_balance(self, name):
        ret = self.get_customer(name)
        if ret is not None:
            return {'balance': ret['money'],
                'overdraft': ret['limitMoney']
                }
        return None

    def get_inbound_gateway_info(self, name):
        ret = self.get_inbound_gateway(name)
        if ret is not None:
            return {
                'ips': ret['remoteIps'],
                'ports': ret['capacity'],
                'route_groups': ret['routingGatewayGroups'],
            }
        return None






if __name__ == '__main__':
    api = VOSAPI('https://127.0.0.1:7133')

    #cust = api.get_customer('vivan')
    #print(cust)

    #ret, cust = api.create_customer('demo2')
    #print('ret:%s cust:%s' % (ret, cust))

    #rate = api.get_rate_group('ttt')
    #print(rate)

    #ret, rate = api.create_rate_group('ttt')
    #print(rate)

    #ret = api.delete_rate_group('ttt')
    #print(ret)

    #ret = api.delete_customer('demo-cust')
    #print(ret)

    #ret = api.init_customer('test001')
    #print(ret)

    #ret = api.get_inbound_gateway('test001')
    #ret, gw = api.create_inbound_gateway('test001')
    #print(ret)
    #ret = api.init_customer('test001')
    #print('init customer result:%s' % ret)

    #ret = api.destory_customer('test001')
    #api.credit_customer('test001', 11)
    #ret = api.get_customer('test001')
    #print(ret)
    #ret = api.update_ips('test001', '33.33.44.44')
    #ret = api.update_ports('test001', 100)
    ret = api.get_balance('test')
    print(ret)










