# -*- coding: utf-8 -*-
#!/usr/bin/python

import os, time
import subprocess
from flask import Flask, jsonify, request

from call_manager import CallManager

import logging.config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('web')


manager = CallManager('portal.3trunks.net')

class CallManagerFlaskApp(Flask):
  def run(self, host=None, port=None, debug=None, load_dotenv=True, **options):
    manager.on_start()

    #if not self.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
    super(CallManagerFlaskApp, self).run(host=host, port=port, debug=debug, load_dotenv=load_dotenv, **options)

app = CallManagerFlaskApp(__name__)


@app.route('/')
def root_path():
    return 'call manager server'


def _get_field(data, field):
    if field in data:
        return data[field]
    else:
        return None


@app.route('/call/connect', methods=['POST'])
def on_call_connect():
    """
    update call connect event
    :return:
    """

    req = request.get_json()
    number = _get_field(req, 'number')
    src_ip = _get_field(req, 'src_ip')
    file = _get_field(req, 'file')
    if number is not None and number != '':
        manager.on_connect(src_ip, number, file)
        logger.info('call:%s via src ip:%s connect to file:%s' % (number, src_ip, file))
    return jsonify({'code': 0})



@app.route('/call/detail', methods=['GET'])
def get_call_detail():
    """
    get call detail
    :return:
    """
    number = request.args.get('number')
    src_ip = request.args.get('src_ip')

    connect_via_trunk = manager.need_connect_via_trunk(number)
    is_block = manager.is_number_block(number)
    call_model = manager.get_feature_number_call_model(number)
    asr = manager.get_asr(src_ip)

    call_data = manager.get_call_data(number)
    try_count = call_data.try_count
    connect_time = call_data.connect_time

    logger.info('query call details for number: %s  via src ip:%s try count: %s connect_time:%s connect_via_trunk: %s is_block: %s call model: %s' % (number,src_ip, try_count, connect_time, connect_via_trunk, is_block, call_model))
    return jsonify({'code': 0, 'data': {'connect_via_trunk': connect_via_trunk,
                                        'is_blocked': is_block,
                                        'call_model': call_model,
                                        'is_connected': connect_via_trunk}})


if __name__ == '__main__':
    app.run('0.0.0.0', 8080, debug=False)