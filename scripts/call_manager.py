# -*- coding: utf-8 -*-
#!/usr/bin/python

from datetime import datetime
import time, sys
import random
import requests
import logging, traceback

if sys.version_info.major == 2:   # Python 2
    import thread
else:                             # Python 3
    import _thread as thread

import logging.config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('manager')


class CallData(object):
    def __init__(self, number):
        self.number = number
        self.init_time = time.time()
        self.connect_time = None
        self.try_count = 0



class CallManager(object):
    def __init__(self, host):
        self._connected_map = {}
        self._config = None
        self._inbound_ips_map = {}
        self._prefix_map = {}
        self._new_feature_numbers = []
        self._call_logs = []
        self._error_files = []
        self._api_host = host
        self.sync_config()


    def sync_config(self):
        try:
            logger.info('sync config from: %s' % self._api_host)
            url = 'https://%s/voip/config/cm?country=%s' % (self._api_host, '86')
            #logger.info('url:%s' % url)
            resp = requests.get(url=url, verify=False)
            if resp.status_code == 200:
                result = resp.json()
                if result['code'] == 'OK':
                    self._config = result['data']

                    self._inbound_ips_map.clear()
                    if 'inbound_ips' in self._config:
                        for item in self._config['inbound_ips']:
                            self._inbound_ips_map[item['ip']] = item

                    self._prefix_map.clear()
                    if 'prefixes' in self._config:
                        for item in self._config['prefixes']:
                            self._prefix_map[item['prefix']] = item

                    if 'error_files' in self._config:
                        self._error_files = self._config['error_files']

        except Exception as e:
            logger.error('sync config error:%s' % e)
            
    def upload_call_logs(self):
        try:
            logger.info('upload call logs to: %s' % self._api_host)
            url = 'https://%s/voip/call_log/upload' % self._api_host
            #logger.info('url:%s' % url)
            logs = self._call_logs
            self._call_logs = []
            resp = requests.post(url=url, verify=False, json=logs)
            if resp.status_code == 200:
                result = resp.json()
                if result['code'] != 'OK':
                    logger.error('upload call logs error')
        except Exception as e:
            logger.error('sync config error:%s' % e)


    def upload_feature_number(self, numbers):
        try:
            logger.info('upload %s feature numbers' % len(numbers))
            url = 'https://%s/voip/feature_number/upload' % self._api_host
            resp = requests.post(url=url, verify=False, json={'country': 86, 'numbers': numbers})
            if resp.status_code == 200:
                result = resp.json()
                if result['code'] == 'OK':
                    logger.info(' -- upload feature number success')
                else:
                    logger.error(' -- upload feature number error')
        except Exception as e:
            logger.error(' -- upload feature number error:%s' % e)


    def _get_feature_number(self, dataset, number):
        for item in dataset:
            if item['number'] == number:
                return item

        return None

    def get_feature_number(self, number):
        if self._config is None:
            return None
        if 'feature_numbers' in self._config:
            return self._get_feature_number(self._config['feature_numbers'], number)
        return None


    def on_connect(self, prefix, number, file, gateway):
        """
        update number latest connect time
        :param number:
        :return:
        """
        if number not in self._connected_map:
            self._connected_map[number] = CallData(number)

        data = self._connected_map[number]
        data.connect_time = time.time()

        # append call log
        item = {
            'prefix': prefix,
            'number': number,
            'file': file,
            'gateway': gateway
        }
        self._call_logs.append(item)


    def get_call_config(self, prefix, number):
        """
        get call config data
        :param number:
        :return:
        """
        if number not in self._connected_map:
            self._connected_map[number] = CallData(number)
        data = self._connected_map[number]
        # count try cnt
        data.try_count = data.try_count + 1
        #catch mutli try count number
        if data.try_count >= 5:
            if number not in self._new_feature_numbers:
                self._new_feature_numbers.append(number)

        config = {
            'asr': 0.18,
            'silent': 0,
            'ringtone': 0,
            'enable_sky_net': False,
            'connect_via_trunk': False,
            'is_blocked': False,
            'is_connected': False,  # will delete future
            'name': 'None',
            'prefix': '',
            'error_files': self._error_files
        }

        enable_sky_net = False
        mix_ratio = 0
        if prefix is None or prefix == '':#old version do not provider src ip
            enable_sky_net = True
            config['enable_sky_net'] = True
        else:
            if prefix in self._prefix_map:
                item = self._prefix_map[prefix]
                # if have src ip config, set asr and enable_sky_net
                config['asr'] = item['asr']
                config['silent'] = item['silent']
                if item['ringtone']:
                    config['ringtone'] = 1
                else:
                    config['ringtone'] = 0

                config['enable_sky_net'] = item['enable_sky_net']
                config['name'] = item['name']
                config['prefix'] = item['prefix']

                enable_sky_net = item['enable_sky_net']
                mix_ratio = item['mix_ratio']

        if enable_sky_net:
            # check feature number
            fn = self.get_feature_number(number)
            #it is not feature number or feature is auto model then use default logic to handle config['connect_via_trunk']
            if fn is None or fn['call_model'] == 'Auto':
                # try call a number 3 times, we make it connect
                if data.try_count >= 3:
                    connect = random.random()
                    if connect <= 0.7:
                        config['connect_via_trunk'] = True

                if data.try_count >= 4:
                    connect = random.random()
                    if connect <= 0.9:
                        config['connect_via_trunk'] = True

                if data.try_count >= 5:
                    config['connect_via_trunk'] = True

                # if number is connected, we make it connect
                if data.connect_time is not None:
                    config['connect_via_trunk'] = True

                # if mix_ratio > 0 then check connect_via_trunk set true
                if not config['connect_via_trunk'] and mix_ratio > 0:
                    if random.random() <= mix_ratio:
                        config['connect_via_trunk'] = True

            elif fn['call_model'] == 'Direct':
                config['connect_via_trunk'] = True

            elif fn['call_model'] == 'Block':
                config['connect_via_trunk'] = False
                config['is_blocked'] = True
        else:
            config['connect_via_trunk'] = False
            if data.connect_time is not None: #if connected in 1 hour, do not connect the number anymore
                config['asr'] = 0

        # make old version work
        config['is_connected'] = config['connect_via_trunk']

        return config


    def get_call_data(self, number):
        if number in self._connected_map:
            return self._connected_map[number]
        return None

    def on_start(self):
        register_thread = thread.start_new_thread(self._on_start, (1,))

    def _on_start(self, args):
        # wait 5 secends to let flask run
        time.sleep(5)

        self.start_clear_cache_process()

    def start_clear_cache_process(self):
        logger.info('start update local info process')
        self._clear_cache__thread = thread.start_new_thread(self.clear_cache_process, (1,))

    def clear_cache_process(self, args):
        while True:
            try:
                logger.info('clear cache')
                to_delete = []
                ts = time.time()
                multi_tried_calls = 0
                for key in self._connected_map.keys():
                    data = self._connected_map[key]
                    #logger.debug('call passed:%s' % (ts - self._connected_map[key]))
                    # connected 60 minutes ago, reset call data
                    if data.connect_time is not None and ts - data.connect_time > 60 * 60:
                        to_delete.append(key)

                    # try count > 3 and inited 20 minutes ago delete.
                    if ts - data.init_time > 20 * 60:
                        to_delete.append(key)

                    if data.try_count >= 3:
                        multi_tried_calls = multi_tried_calls + 1

                for key in to_delete:
                    del self._connected_map[key]


                if len(self._new_feature_numbers) > 0:
                    #upload number to server
                    self.upload_feature_number(self._new_feature_numbers)
                    self._new_feature_numbers.clear()

                logger.info('cache size: %s deleted: %s multi_tried_calls: %s' % (len(self._connected_map), len(to_delete), multi_tried_calls))

                self.sync_config()
                self.upload_call_logs()
                time.sleep(1 * 60)
            except Exception as e:
                logger.error('process error:%s' % e)









