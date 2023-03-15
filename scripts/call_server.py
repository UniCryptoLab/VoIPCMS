# -*- coding: utf-8 -*-
#!/usr/bin/python

import os, time
import subprocess
import argparse
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
    prefix = _get_field(req, 'prefix')
    gateway = _get_field(req, 'gateway')
    file = _get_field(req, 'file')
    if number is not None and number != '':
        manager.on_connect(prefix, number, file, gateway)
        logger.info('-- call:%s via prefix: %s connect to file:%s gw:%s ' % (number, prefix, file, gateway))
    return jsonify({'code': 0})

@app.route('/call/config', methods=['GET'])
def get_call_config():
    """
    get call detail
    :return:
    """
    number = request.args.get('number')
    prefix = request.args.get('prefix')

    config = manager.get_call_config(prefix, number)

    call_data = manager.get_call_data(number)
    try_count = call_data.try_count
    connect_time = call_data.connect_time

    logger.info('query call config for number: %s  via prefix: %s try count: %s connect_time:%s config: %s ' % (number, prefix, try_count, connect_time, config))
    return jsonify({'code': 0, 'data': config})

@app.route('/call/detail', methods=['GET'])
def get_call_detail():
    """
    get call detail
    :return:
    """
    number = request.args.get('number')
    prefix = request.args.get('prefix')

    config = manager.get_call_config(prefix, number)

    call_data = manager.get_call_data(number)
    try_count = call_data.try_count
    connect_time = call_data.connect_time

    logger.info('query call config for number: %s  via prefix: %s try count: %s connect_time:%s config: %s ' % (number, prefix, try_count, connect_time, config))
    return jsonify({'code': 0, 'data': config})


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('-p', '--port', default=8080, help='bind port')
    args = argp.parse_args()
    app.run('0.0.0.0', args.port, debug=False)