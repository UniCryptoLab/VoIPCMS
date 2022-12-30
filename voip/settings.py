#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.conf import settings
gettext = lambda s: s


UNIPAYMENT_CLIENT_ID = getattr(settings,
                                      'UNIPAYMENT_CLIENT_ID',
                                      'CLIENTID')
UNIPAYMENT_CLIENT_SECRET = getattr(settings,
                                      'UNIPAYMENT_CLIENT_SECRET',
                                      'CLIENTSECRET')
UNIPAYMENT_APP_ID = getattr(settings,
                                      'UNIPAYMENT_APP_ID',
                                      'APPID')

SKYPE_USERNAME = getattr(settings,
                                      'SKYPE_USERNAME',
                                      'SKYPEUSERNAME')

SKYPE_PASS = getattr(settings,
                                      'SKYPE_PASS',
                                      'SKYPEPASS')

CMS_HOST = getattr(settings,
                                      'CMS_HOST',
                                      '127.0.0.1')