#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests

class GatewayAPI(object):
    def __init__(self, gateway):
        self._gateway = gateway
        self._host = gateway.ip
        self._port = 8080

    def update_system(self):
        """
        when plotter config change, notify plotter
        :param service_name:
        :return:
        """
        response = requests.get('http://%s:%s/update' % (self._host, self._port))
        return response.json()

    def restart_system(self, service_name):
        """
        restart service srv.plotter srv.hpool etc
        :param service_name:
        :return:
        """
        query = {'service_name': service_name}
        response = requests.get('http://%s:%s/restart' % (self._host, self._port), params=query)

        return response.json()
