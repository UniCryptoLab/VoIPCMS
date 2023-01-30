#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.http import HttpResponse, HttpResponseNotFound, Http404 ,HttpResponseRedirect
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.utils import timezone

from common import Response,Success,Error, json_response, _json_content
from common import get_client_ip

from unipayment import UniPaymentClient, ApiException
from .models import Recharge, FeatureNumber, InboundGateway, Customer, CallLog
from . import settings

import logging, traceback
logger = logging.getLogger(__name__)


@csrf_exempt
def handle_payment_notify(request):
    try:
        if request.method == "GET":
            raise Exception("GET not support")
        else:
            #client_ip = get_client_ip(request)
            notify = json.loads(request.body)
            client = UniPaymentClient(settings.UNIPAYMENT_CLIENT_ID, settings.UNIPAYMENT_CLIENT_SECRET)
            try:
                check_ipn_response = client.check_ipn(notify)
                check_ipn_response.code ='OK'
                if check_ipn_response.code == 'OK':
                    recharge = Recharge.objects.get_recharge_by_invoice_id(notify['invoice_id'])
                    if recharge is not None:
                        # ipn is valid, we can handle status
                        logger.info('recharge:%s invoice:%s event:%s status:%s error_status:%s' % (recharge.pk, notify['invoice_id'], notify['event'], notify['status'], notify['error_status']))
                        if notify['status'] == 'Confirmed':
                            # payment is confirmed, we can process recharge
                            if not recharge.is_gateway_confirmed:
                                recharge.is_gateway_confirmed = True
                                recharge.gateway_confirmed_time = timezone.now()
                                recharge.save()
                                logger.info('recharge:%s invoice_id:%s confirmed' % (recharge.pk, recharge.invoice_id))
                        elif notify['status'] == 'Expired':
                            # payment is expired, we expire recharge
                            if not recharge.is_expired:
                                recharge.is_expired = True
                                recharge.expired_time = timezone.now()
                                recharge.save()
                                logger.info('recharge:%s invoice_id:%s expired' % (recharge.pk, recharge.invoice_id))
                else:
                    logger.error('invoice:%s is not valid' % notify['invoice_id'])
            except ApiException as e:
                logger.error('check invoice:%s error: %s' % (notify['invoice_id'], e))
            return HttpResponse('SUCCESS')
    except Exception as e:
        logger.error('process unipayment notify error: %s' % e)
        return HttpResponse('FAIL')



def get_call_manager_config(request):
    try:
        if request.method == "POST":
            raise Exception("POST not support")
        else:
            client_ip = get_client_ip(request)
            country = request.GET.get("country", None)
            if country is None:
                raise Exception("please provider country")
            feature_numbers = FeatureNumber.objects.filter(country=country).all()
            inbound_ips = InboundGateway.objects.all()
            prefixes = Customer.objects.all()
            data = {
                'feature_numbers': [item.to_dict() for item in feature_numbers],
                'inbound_ips': [item.to_dict() for item in inbound_ips],
                'prefixes': [item.to_dict() for item in prefixes]
            }
            return json_response(Success(data))
    except Exception as e:
        logger.error(traceback.format_exc())
        return json_response(Error(str(e)))


@csrf_exempt
def upload_feature_numbers(request):
    try:
        if request.method == "GET":
            raise Exception("GET not support")
        else:
            client_ip = get_client_ip(request)
            data = json.loads(request.body)

            FeatureNumber.objects.upload_numbers(data['country'], data['numbers'])
            return json_response(Success())
    except Exception as e:
        logger.error(traceback.format_exc())
        return json_response(Error(str(e)))


@csrf_exempt
def upload_call_logs(request):
    try:
        if request.method == "GET":
            raise Exception("GET not support")
        else:
            client_ip = get_client_ip(request)
            data = json.loads(request.body)
            print(data)
            for item in data:
                CallLog.objects.upload_call_log(item['prefix'], item['number'], item['file'], item['gateway'])
            return json_response(Success())
    except Exception as e:
        logger.error(traceback.format_exc())
        return json_response(Error(str(e)))

def api_api_check(request):
    try:
        if request.method == "POST":
            raise Exception("POST not support")
        else:
            client_ip = get_client_ip(request)
            api_name = request.GET.get("api_name", None)
            if api_name is None:
                raise Exception("please provider api_name")
            server, api = get_api(client_ip, api_name)
            return json_response(Success())
    except Exception as e:
        logger.error(traceback.format_exc())
        return json_response(Error(str(e)))
