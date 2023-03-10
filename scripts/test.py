#!/usr/bin/env python3

import os, sys, re
import random
import requests

from dotenv import load_dotenv
from asterisk.agi import *

load_dotenv()

ring_type = int(os.getenv('RING_TYPE', 0))

wait_normal = int(os.getenv('WAIT_AVG', 12))
wait_range = int(os.getenv('WAIT_RANGE', 8))
wait_timeout = int(os.getenv('WAIT_TIMEOUT', 55))

connect_target = float(os.getenv('CONNECT_ASR', 0.18))
pdd_normal = int(os.getenv('PDD_NORMAL', 2))
pdd_range = int(os.getenv('PDD_RANGE', 2))

not_connect_busy = float(os.getenv('NO_CONNECT_BUSY', 0.05))
not_connect_decline = float(os.getenv('NO_CONNECT_DECLINE', 0.1))
not_connect_poweroff = float(os.getenv('NO_CONNECT_POWEROFF', 0.05))
not_connect_notreach = float(os.getenv('NO_CONNECT_NOTREACH', 0.05))

cm_host = os.getenv('CM_HOST', '127.0.0.1:8080')
dst_channel = os.getenv('DEST_CHANNEL', 'sbc01')
gateway = os.getenv('GATEWAY', 'gw-01')

mobile_number_re = '^1(3[0-9]|4[579]|5[0-3,5-9]|6[6]|7[0135678]|8[0-9]|9[89])\d{8}$'


def is_wave(fn):
    if fn.endswith('wav'):
        return True
    return False


def get_ivr_list(error_files):
    files = os.listdir('/opt/asterisk/sound')
    files_wav_iterator = filter(is_wave, files)
    files_wav = list(files_wav_iterator)
    ret = [file.split('.')[0] for file in files_wav]
    def fun1(s): return s if s not in error_files else None
    return list(filter(fun1, ret))


def get_ivr_file(error_files):
    files = get_ivr_list(error_files)
    #agi.verbose("****** files:%s" % files)
    cnt = len(files)
    r = random.random()
    v = int(cnt * r)
    #agi.verbose("cnt:%s r:% file v:%s" % (cnt, r, v))
    return files[v]


def get_randam_wait(normal, range):
    diff = range * random.random() - range / 2
    wait = normal + diff
    return wait


def get_call_config(prefix, number):
    try:
        url = 'http://%s/call/config?number=%s&prefix=%s' % (cm_host, number, prefix)
        # agi.verbose("url: %s" % url)
        resp = requests.get(url=url, verify=False)
        if resp.status_code == 200:
            result = resp.json()
            if result['code'] == 0:
                return result['data']
        return None
    except Exception as e:
        agi.verbose("get call:%s config error:%s" % (number, e))
        return None


def on_call_connect(prefix, number, file):
    try:
        url = 'http://%s/call/connect' % cm_host
        resp = requests.post(url=url, verify=False,
                             json={'prefix': prefix, 'number': number, 'file': file, 'gateway': gateway})
    except Exception as e:
        agi.verbose("on connect call:%s error:%s" % (number, e))


def get_value(dict, field, val):
    if dict is None:
        return val
    if field in dict:
        return dict[field]
    else:
        return val


agi = AGI()

# agi.verbose("python agi started")
callerId = agi.env['agi_callerid']
caller_prefixes = [852244, 852241, 852225, 852236, 852244, 852267, 852263, 852233, 852245, 852278, 852259]
caller_prefix_cnt = len(caller_prefixes)
caller_prefix_idx = int(caller_prefix_cnt * random.random())
callerId = '00%s%s' % (caller_prefixes[caller_prefix_idx], ('%s' % int(random.random() * 100000)).zfill(5))
agi.set_callerid(callerId)

src_ip = agi.get_variable('src_ip')
agi.verbose("---- call from ip:%s %s -> %s ----" % (src_ip, agi.env['agi_callerid'], agi.env['agi_dnid']))

dnid = agi.env['agi_dnid']
prefix = ''

call_config = None
need_get_config = True

if '3T' in dnid:
    need_get_config = False #if traffic is internal
    dnid = dnid.replace('3T', '') #generate the normal number

# CN9998613922334455
if dnid[0].isalpha():
    prefix = dnid[:5][2:]  # 999
    dnid = dnid[5:]  #

if need_get_config:
    call_config = get_call_config(prefix, dnid)

error_files = get_value(call_config, 'error_files', [])
agi.verbose("error_files:%s " % error_files)

if call_config is not None and get_value(call_config, 'is_block', False):
    # number is blocked
    agi.verbose("number:%s is blocked % dnid")
    agi.set_variable('TCode', 19)

elif call_config is not None and get_value(call_config, 'connect_via_trunk', False):
    # if need route to trunk
    agi.verbose("connect call via trunk, prefix: %s from: %s to: %s" % (prefix, callerId, dnid))
    agi.appexec('dial', 'SIP/%s/%s,60' % (dst_channel, dnid))

else:
    agi.verbose("connect call via local, prefix: %s from: %s to: %s" % (prefix, callerId, dnid))

    # config
    connect_target = get_value(call_config, 'asr', connect_target)
    ring_type = get_value(call_config, 'ringtone', ring_type)
    agi.verbose('call config asr:%s busy:%s decline:%s power off:%s not reach:%s ring:%s' % (
        connect_target, not_connect_busy, not_connect_decline, not_connect_poweroff, not_connect_notreach, ring_type))

    # check phone number
    if not dnid.startswith('86'):
        agi.hangup()

    result = re.findall(mobile_number_re, dnid[2:])
    if not result:
        # error number
        #agi.appexec('progress')
        #agi.appexec('playback', '/opt/asterisk/sound_system/telecom_errornumber,noanswer')
        agi.appexec('wait', 1)
        agi.set_variable('TCode', 1)
    else:
        # good number
        connect = random.random()
        agi.verbose("target asr:%s real time value:%s " % (connect_target, connect))
        wait_ring = pdd_normal + random.random() * pdd_range

        if connect <= connect_target:
            # wait seconds
            diff = wait_range * random.random() - wait_range / 2
            wait = wait_normal + diff
            agi.verbose("CONNECT after ring :%s seconds" % wait)
            if ring_type == 0:
                agi.appexec('wait', wait_ring)
                agi.appexec('ringing')
                agi.appexec('wait', wait)
            else:
                agi.appexec('wait', wait_ring)
                agi.appexec('progress')
                agi.appexec('wait', 1)
                agi.appexec('playtones', 'ring')
                agi.appexec('wait', wait)
                agi.appexec('stopplaytones')

            # select file with random
            files_target = get_ivr_file(error_files)
            agi.verbose("files target:%s" % files_target)
            agi.appexec('answer')
            agi.appexec('wait', 2)
            on_call_connect(prefix, dnid, files_target)
            agi.appexec('playback', '/opt/asterisk/sound/%s' % files_target)
            agi.appexec('wait', 3)
            agi.set_variable('TCode', 16)

        else:
            # not connect, ring time out / decline / poweroff / noreach
            r = random.random()
            carrier = 'telecom'
            agi.verbose("NOCONNECT situation value:%s" % r)
            if r <= not_connect_busy:  # calee decline the call
                agi.verbose("-- will busy direct")
                agi.appexec('wait', 3)
                agi.appexec('progress')
                agi.appexec('playback', '/opt/asterisk/sound_system/%s_busy,noanswer' % carrier)
                agi.appexec('wait', 1)
                agi.set_variable('TCode', 19)

            if r > not_connect_busy and r <= (not_connect_busy + not_connect_decline):  # calee decline the call
                wait = get_randam_wait(7, 4)
                agi.verbose("-- will dicline after ring :%s seconds" % wait)
                if ring_type == 0:
                    agi.appexec('wait', wait_ring)
                    agi.appexec('ringing')
                    agi.appexec('wait', wait)
                    agi.appexec('progress')
                else:
                    agi.appexec('wait', wait_ring)
                    agi.appexec('progress')
                    agi.appexec('wait', 1)
                    agi.appexec('playtones', 'ring')
                    agi.appexec('wait', wait)
                    agi.appexec('stopplaytones')
                agi.appexec('playback', '/opt/asterisk/sound_system/%s_busy,noanswer' % carrier)
                agi.appexec('wait', 1)
                agi.set_variable('TCode', 19)

            if r > (not_connect_busy + not_connect_decline) and r <= (
                    not_connect_busy + not_connect_decline + not_connect_poweroff):  # cell is power off
                wait = get_randam_wait(4, 0)
                agi.verbose("-- will poweroff after :%s seconds" % wait)
                agi.appexec('wait', wait)
                agi.appexec('progress')
                agi.appexec('playback', '/opt/asterisk/sound_system/%s_poweroff,noanswer' % carrier)
                agi.appexec('wait', 1)
                agi.set_variable('TCode', 19)

            if r > (not_connect_busy + not_connect_decline + not_connect_poweroff) and r <= (
                    not_connect_busy + not_connect_decline + not_connect_poweroff + not_connect_notreach):  # number can not reach
                wait = get_randam_wait(4, 0)
                agi.verbose("-- will noreach after :%s seconds" % wait)
                agi.appexec('wait', wait)
                agi.appexec('progress')
                agi.appexec('playback', '/opt/asterisk/sound_system/%s_notreach,noanswer' % carrier)
                agi.appexec('wait', 1)
                agi.set_variable('TCode', 19)

            if r > (
                    not_connect_busy + not_connect_decline + not_connect_poweroff + not_connect_notreach):  # ring timeout
                wait = wait_timeout
                agi.verbose("-- will timeout after ring :%s seconds" % wait)

                if ring_type == 0:
                    agi.appexec('wait', wait_ring)
                    agi.appexec('ringing')
                    agi.appexec('wait', wait)
                    agi.appexec('progress')
                else:
                    agi.appexec('wait', wait_ring)
                    agi.appexec('progress')
                    agi.appexec('wait', 1)
                    agi.appexec('playtones', 'ring')
                    agi.appexec('wait', wait)
                    agi.appexec('stopplaytones')
                agi.appexec('playback', '/opt/asterisk/sound_system/%s_timeout,noanswer' % carrier)
                agi.appexec('wait', 1)
                agi.set_variable('TCode', 19)







