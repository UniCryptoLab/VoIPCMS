# -*- coding: utf-8 -*-
#!/usr/bin/python

import os, time
import subprocess
from flask import Flask, jsonify, request

from call_manager import CallManager

import logging.config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('web')


manager = CallManager()

class CallManagerFlaskApp(Flask):
  def run(self, host=None, port=None, debug=None, load_dotenv=True, **options):
    manager.on_start()

    #if not self.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
    super(CallManagerFlaskApp, self).run(host=host, port=port, debug=debug, load_dotenv=load_dotenv, **options)

app = CallManagerFlaskApp(__name__)


@app.route('/')
def root_path():
    return 'call manager server'


@app.route('/call/connect', methods=['POST'])
def on_call_connect():
    """
    update call connect event
    :return:
    """

    number = request.get_json()['number']
    if number is not None and number != '':
        manager.on_connect(number)
        logger.info('call:%s connected' % number)
    return jsonify({'code': 0})


@app.route('/call/detail', methods=['GET'])
def get_call_detail():
    """
    get call detail
    :return:
    """
    number = request.args.get('number')
    connect_via_trunk = manager.need_connect_via_trunk(number)
    is_block = manager.is_number_block(number)

    call_data = manager.get_call_data(number)
    try_count = call_data.try_count
    connect_time = call_data.connect_time

    logger.info('query call details for number: %s  try number: %s connect_time:%s connect_via_trunk: %s' % (number, try_count, connect_time, connect_via_trunk))
    return jsonify({'code': 0, 'data': {'connect_via_trunk': connect_via_trunk,
                                        'is_blocked': is_block,
                                        'is_connected': connect_via_trunk}})


if __name__ == '__main__':
    app.run('0.0.0.0', 8080, debug=False)