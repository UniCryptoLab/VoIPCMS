# -*- coding: utf-8 -*-
#!/usr/bin/python

import os, time
import subprocess
from flask import send_file, send_from_directory
from flask import Flask, jsonify, request


app = Flask(__name__)



@app.route('/')
def root_path():
    return 'files server'


@app.route("/ivr/<filename>", methods=['GET'])
def download_file(filename):
    if filename is None or filename == '':
        return 'please input file id'
    fn = '/opt/data/files/%s.wav' % filename
    if not os.path.isfile(fn):
        return 'file not exist'
    return send_from_directory('/opt/data/files', '%s.wav' % filename, as_attachment=True)


if __name__ == '__main__':
    app.run('0.0.0.0', 8080, debug=False)