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
            #logger.debug('config:%s' % self._config)
        except Exception as e:
            logger.error('sync config error:%s' % e)

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


    def on_connect(self, src_ip, number, file):
        """
        update number latest connect time
        :param number:
        :return:
        """
        if number not in self._connected_map:
            self._connected_map[number] = CallData(number)

        data = self._connected_map[number]
        data.connect_time = time.time()

    def is_number_block(self, number):
        fn = self.get_feature_number(number)
        if fn is not None:
            return fn['call_model'] == 'Block'
        return False

    def get_feature_number_call_model(self, number):
        fn = self.get_feature_number(number)
        if fn is not None:
            return fn['call_model']
        return None

    def need_connect_via_trunk(self, number):
        """
        check if number need connect through trunk
        :param number:
        :return:
        """
        if number not in self._connected_map:
            self._connected_map[number] = CallData(number)
        data = self._connected_map[number]
        # count try cnt
        data.try_count = data.try_count + 1

        # check feature number
        fn = self.get_feature_number(number)
        if fn is not None:
            call_model = fn['call_model']
            if call_model == 'Direct':
                return True
            elif call_model == 'Bypass':
                return False
            elif call_model == 'Block':
                return False

        #AUTO model
        # try call a number 3 times, we make it connect
        if data.try_count >= 3:
            connect = random.random()
            if connect <= 0.7:
                return True

        if data.try_count >= 4:
            connect = random.random()
            if connect <= 0.9:
                return True

        if data.try_count >= 5:
            return True

        # if number is connected, we make it connect
        if data.connect_time is not None:
            return True

        return False


    def get_asr(self, src_ip):
        if src_ip is None or src_ip == '':
            return 0.18

        if self._config is None:
            return 0.18

        if 'asr' in self._config:
            if src_ip in self._config['asr']:
                return self._config['asr'][src_ip]

        return 0.18

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
                logger.info('start clear cache....')
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


                logger.info('cache size: %s deleted: %s multi_tried_calls: %s' % (len(self._connected_map), len(to_delete), multi_tried_calls))

                self.sync_config()
                time.sleep(1 * 60)
            except Exception as e:
                logger.error('process error:%s' % e)









