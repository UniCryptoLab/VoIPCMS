
import sys, os, random, re
import requests
import traceback
import platform
import socket
import subprocess
import threading
import argparse
import pprint
import asterisk.agi
from asterisk.agi import *

from six import PY3
from dotenv import load_dotenv

try:
    import socketserver
except ModuleNotFoundError:
    import SocketServer as socketserver


import logging
import logging.config

logging.config.fileConfig("logging.conf")
logger = logging.getLogger(__name__)


re_code = re.compile(r'(^\d*)\s*(.*)')
re_kv = re.compile(r'(?P<key>\w+)=(?P<value>[^\s]+)\s*(?:\((?P<data>.*)\))*')


class _ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    Provides a variant of the TCPServer that spawns a new thread to handle each
    request.
    """

    @staticmethod
    def get_somaxconn():
        """
        Returns the value of SOMAXCONN configured in the system.
        """
        # determine the OS appropriate management informations base (MIB)
        # name to determine SOMAXCONN
        system = platform.system()
        if "Linux" == system:
            sysctl_mib_somaxconn = "net.core.somaxconn"
            sysctl_output_delimiter = "="
        elif "Darwin" == system:
            sysctl_mib_somaxconn = "kern.ipc.somaxconn"
            sysctl_output_delimiter = ":"
        else:
            raise NotImplementedError(
                "Determining SOMAXCONN is not implemented for {} system.".format(system)
            )
        # run the cmd to determine the SOMAXCONN
        cmd_result = subprocess.check_output(["sysctl", sysctl_mib_somaxconn])

        # parse the output of the cmd to return the value of SOMAXCONN
        return int(cmd_result.decode().split(sysctl_output_delimiter)[-1].strip())

    def __init__(self, *args, **kwargs):
        # adjust request queue size to a saner value for modern systems
        # further adjustments are automatically picked up for kernel
        # settings on server start
        self.request_queue_size = max(socket.SOMAXCONN, self.get_somaxconn())
        self.allow_reuse_address = True
        super().__init__(*args, **kwargs)


class FastAGIServer(_ThreadedTCPServer):
    """
    Provides a FastAGI TCP server to handle requests from Asterisk servers.
    """
    debug = False  # Used to enable various printouts for library development

    def __init__(self, interface='127.0.0.1', port=4573, daemon_threads=True, debug=False):
        """
        Creates the server and binds the client-handler callable.

        `interface` is the address of the interface on which to listen; defaults
        to localhost, but may be any interface on the host or `'0.0.0.0'` for
        all. `port` is the TCP port on which to listen.

        `daemon_threads` indicates whether any threads spawned to handle
        requests should be killed if the main thread dies. (Generally a good
        idea to avoid hung calls keeping the process alive forever)
        `debug` should only be turned on for library development.
        """
        _ThreadedTCPServer.__init__(self, (interface, port), FastAGIHandler)
        self.debug = debug
        self.daemon_threads = daemon_threads
        logger.info("Init FastAGIServer at:%s" % port)


class AGINg(asterisk.agi.AGI):
    def __init__(self, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self._got_sighup = False
        self.stderr.write('ARGS: ')
        self.stderr.write(str(sys.argv))
        self.stderr.write('\n')
        self.env = {}
        self._get_agi_env()
        # signal.signal(signal.SIGHUP, self._handle_sighup)  # handle SIGHUP, only used in

    def _get_agi_env(self):
        while 1:
            line = self.stdin.readline().strip()
            if PY3:
                line = line.decode('utf8')
            self.stderr.write('ENV LINE: ')
            self.stderr.write(line)
            self.stderr.write('\n')
            if line == '':
                # blank line signals end
                break
            key, data = line.split(':')[0], ':'.join(line.split(':')[1:])
            key = key.strip()
            data = data.strip()
            if key != '':
                self.env[key] = data
        #self.stderr.write('class AGI: self.env = ')
        #self.stderr.write(pprint.pformat(self.env))
        #self.stderr.write('\n')

    def send_command(self, command, *args):
        """Send a command to Asterisk"""
        command = command.strip()
        command = '%s %s' % (command, ' '.join(map(str, args)))
        command = command.strip()
        if command[-1] != '\n':
            command += '\n'
        self.stderr.write('    COMMAND: %s' % command)
        self.stdout.write(bytes(command, 'utf-8'))
        self.stdout.flush()

    def get_result(self, stdin=sys.stdin):
        """Read the result of a command from Asterisk"""
        code = 0
        result = {'result': ('', '')}
        line = self.stdin.readline().strip()
        if PY3:
            line = line.decode('utf8')
        self.stderr.write('    RESULT_LINE: %s\n' % line)
        m = re_code.search(line)
        if m:
            code, response = m.groups()
            if code is None or code == '':
                code = 200
            code = int(code)
        if code == 200:
            for key, value, data in re_kv.findall(response):
                result[key] = (value, data)
                # If user hangs up... we get 'hangup' in the data
                if data == 'hangup':
                    raise AGIResultHangup("User hungup during execution")

                if key == 'result' and value == '-1':
                    raise AGIAppError("Error executing application, or hangup")

            self.stderr.write('    RESULT_DICT: %s\n' % pprint.pformat(result))
            return result
        elif code == 510:
            raise AGIInvalidCommand(response)
        elif code == 520:
            usage = [line]
            line = self.stdin.readline().strip()
            line = line.decode('utf8')
            while line[:3] != '520':
                usage.append(line)
                line = self.stdin.readline().strip()
                line = line.decode('utf8')
            usage.append(line)
            usage = '%s\n' % '\n'.join(usage)
            raise AGIUsageError(usage)
        else:
            raise AGIUnknownError(code, 'Unhandled code or undefined response')


class FastAGIHandler(socketserver.StreamRequestHandler):
    # Close connections not finished in 5seconds.
    timeout = 10*60
    mobile_number_re = '^1(3[0-9]|4[579]|5[0-3,5-9]|6[6]|7[0135678]|8[0-9]|9[89])\d{8}$'
    ivr_list = None

    def __init__(self, request, client_address, server):
        load_dotenv()
        self._ring_type = int(os.getenv('RING_TYPE', 0))

        self._cm_host = os.getenv('CM_HOST', '18.142.122.167:8080')
        self._dst_channel = os.getenv('DEST_CHANNEL', 'sbc01')
        self._gateway = os.getenv('GATEWAY', 'gw-01')

        self._wait_normal = int(os.getenv('WAIT_AVG', 12))
        self._wait_range = int(os.getenv('WAIT_RANGE', 8))
        self._wait_timeout = int(os.getenv('WAIT_TIMEOUT', 50)) #55

        self._connect_target = float(os.getenv('CONNECT_ASR', 0.18)) #0.18
        self._pdd_normal = int(os.getenv('PDD_NORMAL', 2))
        self._pdd_range = int(os.getenv('PDD_RANGE', 2))

        self._not_connect_busy = float(os.getenv('NO_CONNECT_BUSY', 0.05)) #0.05
        self._not_connect_decline = float(os.getenv('NO_CONNECT_DECLINE', 0.1)) #0.1
        self._not_connect_poweroff = float(os.getenv('NO_CONNECT_POWEROFF', 0.05)) #0.05
        self._not_connect_notreach = float(os.getenv('NO_CONNECT_NOTREACH', 0.05)) #0.05

        super(FastAGIHandler, self).__init__(request, client_address, server)

    def is_wave(self, fn):
        if fn.endswith('wav'):
            return True
        return False

    def get_ivr_list(self, error_files):
        if FastAGIHandler.ivr_list is None:
            print('load files list from disk')
            files = os.listdir('/opt/asterisk/sound')
            files_wav_iterator = filter(self.is_wave, files)
            files_wav = list(files_wav_iterator)
            FastAGIHandler.ivr_list = [file.split('.')[0] for file in files_wav]

        def fun1(s): return s if s not in error_files else None

        return list(filter(fun1, FastAGIHandler.ivr_list))

    def get_ivr_file(self, error_files):
        files = self.get_ivr_list(error_files)
        # agi.verbose("****** files:%s" % files)
        cnt = len(files)
        r = random.random()
        v = int(cnt * r)
        # agi.verbose("cnt:%s r:% file v:%s" % (cnt, r, v))
        return files[v]

    def get_randam_wait(self, normal, range):
        diff = range * random.random() - range / 2
        wait = normal + diff
        return wait

    def get_call_config(self, prefix, number):
        try:
            url = 'http://%s/call/config?number=%s&prefix=%s' % (self._cm_host, number, prefix)
            # agi.verbose("url: %s" % url)
            resp = requests.get(url=url, verify=False)
            if resp.status_code == 200:
                result = resp.json()
                if result['code'] == 0:
                    return result['data']
            return None
        except Exception as e:
            print("get call:%s config error:%s" % (number, e))
            return None

    def on_call_connect(self, prefix, number, file):
        try:
            url = 'http://%s/call/connect' % self._cm_host
            resp = requests.post(url=url, verify=False,
                                 json={'prefix': prefix, 'number': number, 'file': file, 'gateway': self._gateway})
        except Exception as e:
            print("on connect call:%s error:%s" % (number, e))

    def get_value(self, dict, field, val):
        if dict is None:
            return val
        if field in dict:
            return dict[field]
        else:
            return val

    def get_caller_id(self):
        caller_prefixes = [852244, 852241, 852225, 852236, 852244, 852267, 852263, 852233, 852245, 852278, 852259]
        caller_prefix_cnt = len(caller_prefixes)
        caller_prefix_idx = int(caller_prefix_cnt * random.random())
        callerId = '00%s%s' % (caller_prefixes[caller_prefix_idx], ('%s' % int(random.random() * 100000)).zfill(5))
        return callerId

    def handle(self):
        try:
            agi=AGINg(stdin=self.rfile, stdout=self.wfile, stderr=sys.stderr)

            extension = agi.env['agi_extension']
            if extension == 'h':
                return

            callerId = self.get_caller_id()
            agi.set_callerid(callerId)

            dnid = agi.env['agi_dnid']
            prefix = ''

            call_config = None
            need_get_config = True

            if '3T' in dnid:
                need_get_config = False  # if traffic is internal
                dnid = dnid.replace('3T', '')  # generate the normal number

            # CN9998613922334455
            if dnid[0].isalpha():
                prefix = dnid[:5][2:]  # 999
                dnid = dnid[5:]  #

            if need_get_config:
                call_config = self.get_call_config(prefix, dnid)

            error_files = self.get_value(call_config, 'error_files', [])
            agi.verbose("error_files:%s " % error_files)

            if call_config is not None and self.get_value(call_config, 'is_block', False):
                # number is blocked
                agi.verbose("number:%s is blocked % dnid")
                agi.set_variable('TCode', 19)

            elif call_config is not None and self.get_value(call_config, 'connect_via_trunk', False):
                # if need route to trunk
                agi.verbose("connect call via trunk, prefix: %s from: %s to: %s" % (prefix, callerId, dnid))
                agi.appexec('dial', 'SIP/%s/%s,60' % (self._dst_channel, dnid))

            else:
                agi.verbose("connect call via local, prefix: %s from: %s to: %s" % (prefix, callerId, dnid))

                # config
                connect_target = self.get_value(call_config, 'asr', self._connect_target)
                ring_type = self.get_value(call_config, 'ringtone', self._ring_type)
                wait_normal = self.get_value(call_config, 'wait_normal', self._wait_normal)
                wait_timeout = self.get_value(call_config, 'wait_timeout', self._wait_timeout)

                agi.verbose('**** config asr:%s busy:%s decline:%s power_off:%s not_reach:%s ring_type:%s' % (
                    connect_target, self._not_connect_busy, self._not_connect_decline, self._not_connect_poweroff, self._not_connect_notreach,
                    ring_type))

                # check phone number
                if not dnid.startswith('86'):
                    agi.hangup()
                result = re.findall(FastAGIHandler.mobile_number_re, dnid[2:])

                if not result:
                    # error number
                    # agi.appexec('progress')
                    # agi.appexec('playback', '/opt/asterisk/sound_system/telecom_errornumber,noanswer')
                    agi.appexec('wait', 1)
                    agi.set_variable('TCode', 1)
                else:
                    # good number
                    connect = random.random()
                    if connect <= connect_target:
                        msg = 'connect:%s <= %s, call will connect' % (connect, connect_target)
                    else:
                        msg = 'connect:%s > %s, call will not connect' % (connect, connect_target)
                    agi.verbose(msg)
                    wait_ring = self._pdd_normal + random.random() * self._pdd_range

                    if connect <= connect_target:
                        # wait seconds
                        diff = self._wait_range * random.random() - self._wait_range / 2
                        wait = wait_normal + diff
                        agi.verbose("[CONNECT] after ring :%s seconds" % wait)
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
                        files_target = self.get_ivr_file(error_files)
                        agi.verbose("files target:%s" % files_target)
                        agi.appexec('answer')
                        agi.appexec('wait', 2)
                        self.on_call_connect(prefix, dnid, files_target)
                        agi.appexec('playback', '/opt/asterisk/sound/%s' % files_target)
                        agi.appexec('wait', 3)
                        agi.set_variable('TCode', 16)

                    else:
                        # not connect, ring time out / decline / poweroff / noreach
                        r = random.random()
                        carrier = 'telecom'
                        agi.verbose("[NO CONNECT] value:%s" % r)
                        if r <= self._not_connect_busy:  # calee decline the call
                            agi.verbose("-- will busy direct")
                            agi.appexec('wait', 3)
                            agi.appexec('progress')
                            agi.appexec('playback', '/opt/asterisk/sound_system/%s_busy,noanswer' % carrier)
                            agi.appexec('wait', 1)
                            agi.set_variable('TCode', 19)

                        if r > self._not_connect_busy and r <= (
                                self._not_connect_busy + self._not_connect_decline):  # calee decline the call
                            wait = self.get_randam_wait(7, 4)
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

                        if r > (self._not_connect_busy + self._not_connect_decline) and r <= (
                                self._not_connect_busy + self._not_connect_decline + self._not_connect_poweroff):  # cell is power off
                            wait = self.get_randam_wait(4, 0)
                            agi.verbose("-- will poweroff after :%s seconds" % wait)
                            agi.appexec('wait', wait)
                            agi.appexec('progress')
                            agi.appexec('playback', '/opt/asterisk/sound_system/%s_poweroff,noanswer' % carrier)
                            agi.appexec('wait', 1)
                            agi.set_variable('TCode', 19)

                        if r > (self._not_connect_busy + self._not_connect_decline + self._not_connect_poweroff) and r <= (
                                self._not_connect_busy + self._not_connect_decline + self._not_connect_poweroff + self._not_connect_notreach):  # number can not reach
                            wait = self.get_randam_wait(4, 0)
                            agi.verbose("-- will noreach after :%s seconds" % wait)
                            agi.appexec('wait', wait)
                            agi.appexec('progress')
                            agi.appexec('playback', '/opt/asterisk/sound_system/%s_notreach,noanswer' % carrier)
                            agi.appexec('wait', 1)
                            agi.set_variable('TCode', 19)

                        if r > (
                                self._not_connect_busy + self._not_connect_decline + self._not_connect_poweroff + self._not_connect_notreach):  # ring timeout
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

        except TypeError as e:
            exc_type, exc_value, exc_traceback_obj = sys.exc_info()
            traceback.print_tb(exc_traceback_obj)
            sys.stderr.write('Unable to connect to agi://{} {}\n'.format(self.client_address[0], str(e)))
        except socketserver.socket.timeout as e:
            exc_type, exc_value, exc_traceback_obj = sys.exc_info()
            traceback.print_tb(exc_traceback_obj)
            sys.stderr.write('Timeout receiving data from {}\n'.format(self.client_address))
        except socketserver.socket.error as e:
            exc_type, exc_value, exc_traceback_obj = sys.exc_info()
            traceback.print_tb(exc_traceback_obj)
            sys.stderr.write('Could not open the socket. Is something else listening on this port?\n')
        except Exception as e:
            exc_type, exc_value, exc_traceback_obj = sys.exc_info()
            traceback.print_tb(exc_traceback_obj)
            sys.stderr.write('An unknown error: {}\n'.format(str(e)))



if __name__ == "__main__":

    argp = argparse.ArgumentParser()

    argp.add_argument('-p', '--port', default=4573, help='bind port')
    argp.add_argument('-i', '--interface', default='127.0.0.1', help='bind host')
    args = argp.parse_args()

    server = FastAGIServer(interface=args.interface, port=int(args.port))
    # Keep server running until CTRL-C is pressed.
    server.serve_forever()


