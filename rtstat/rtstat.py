#!/usr/bin/env python3

from datetime import datetime, timedelta
import telnetlib
import argparse
import json
import time

# ============================================================================
# ==== Utility functions =====================================================
# ============================================================================


def sanitize(s):
    """Removes all ASCII control characters but newlines."""
    return "".join([c for c in s if (31 < ord(c) < 127) or (c == '\n')])


def merge_dicts(*dict_args):
    """Merges the dictionaries given in arguments together."""
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def parse_key_value(lines, sep=':'):
    """Parses a list of lines in key-value pair format."""
    kv = {}

    for line in lines:
        level = 0
        pos = -1

        for i in range(len(line)):
            if line[i] == '(':
                level += 1
            elif line[i] == ')':
                level -= 1
            elif (line[i] == sep) and (level == 0):
                pos = i
                break

        k = line[:i].strip()
        v = line[i + 1:].strip()

        if k != '':
            kv[k] = v

    return kv


# ============================================================================
# ==== Router implementations ================================================
# ============================================================================


class TG585v8:
    """Interacts via telnet with a Thomson TG585 v8 router.

    Note that this router is usually found on 192.168.1.254."""

    @staticmethod
    def name():
        return 'Thomson TG585 v8'

    def read(self, s):
        """Reads from the telnet session up until the given string."""
        data = self.conn.read_until(s.encode('utf-8'), self.timeout)
        if not data.decode('utf-8').endswith(s):  # timeout/error?
            raise IOError("Failed to read from telnet session.")
        else:
            return sanitize(data.decode('utf-8')[:-len(s)])

    def write(self, s):
        """Writes a string to the telnet session and then returns."""
        self.conn.write(s.encode('utf-8'))

    def __init__(self, host, port=0, timeout=None,
                 username=None, password=None):
        """Opens and authenticates a telnet session to the router.

        If no username or password are passed, the defaults which should
        give administrator access in non-configured routers are used.

        The TG585v8 router has a simple authentication process like most
        routers. It will also display a fancy header upon logging in, so
        we can just skip over all that and seek to the next prompt. Note
        the prompt is known to be in either of the two formats below:

            `{Username}=>`             for top-level commands
            `{Username}[group]=>`      when inside a command group

        Upon login before any commands it will be in the first format.
        """
        self.conn = telnetlib.Telnet(host=host, port=port)
        self.username = username or 'Administrator'
        self.password = password or ''
        self.timeout = timeout

        self.read('Username : ')
        self.write(self.username + '\r\n')
        self.read('Password : ')
        self.write(self.password + '\r\n')
        self.connected = True

        self.read('{{{0}}}=>'.format(self.username))

    def send(self, command):
        """Sends a command to the router and returns the output.

        The output is defined as the data received on the telnet session
        from the end of the command to the start of the next prompt. The
        output will be empty if the command does not emit any data, e.g.
        it is a `cd`-like command that simply enters a command group.
        """
        self.write(command + '\r\n')
        self.read('\r\n')  # seek to prompt end
        return self.read('{{{0}}}'.format(self.username))

    def __exit__(self, type, value, traceback):
        if self.connected:
            self.write('exit\r\n')
        self.conn.close()

    def __enter__(self):
        return self

    def reset_level(self):
        """Navigates to the top-level command group."""
        for _ in range(4):  # arbitrary max depth
            self.send('..')

    def keepalive(self):
        """Keeps the telnet connection active."""
        self.send('help')  # always works

    def get_xdsl_info(self):
        """Gets the current XDSL information for this router."""
        self.reset_level()

        lines = self.send('xdsl info').split('\n')
        kv = parse_key_value(lines)

        uptime_str = kv['Up time (Days hh:mm:ss)']
        days = int(uptime_str.split(',')[0].strip().split(' ')[0])
        hms = uptime_str.split(',')[1].strip()
        t = datetime.strptime(hms, '%H:%M:%S')
        uptime = days * 3600 * 24 + t.hour * 3600 + t.minute * 60 + t.second

        bandwidth_str = kv['Bandwidth (Down/Up - kbit/s)']
        bwd = 1000 * int(bandwidth_str.split('/')[0]) // 8
        bwu = 1000 * int(bandwidth_str.split('/')[1]) // 8

        return {
            'xdsl-info': {
                'state': kv['Modem state'],
                'uptime': uptime,
                'type': kv['xDSL Type'],
                'bandwidth-down': bwd,
                'bandwidth-up': bwu
            }
        }

    def get_iflist_info(self):
        """Gets the current iflist information for this router."""
        self.reset_level()

        lines = self.send('ip iflist').split('\n')[1:]  # remove header line
        info = {}

        for line in lines:
            line = ' '.join(line.replace('.', '').split())

            if line != '':
                tokens = line.split()

                info[tokens[2]] = {
                    'tx': int(tokens[4]),
                    'rx': int(tokens[5])
                }

        return {
            'iflist': info
        }

    def get_all_info(self):
        """Gets all current information for this router."""
        return merge_dicts(
            self.get_xdsl_info(),
            self.get_iflist_info()
        )


ROUTERS = [
    'TG585v8'
]


# ============================================================================
# ==== User interface ========================================================
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Router Statistics Tool.")

    parser.add_argument('-m', '--router', metavar='', required=True,
                        help="router model and version to assume",
                        choices=ROUTERS)

    parser.add_argument('-r', '--host', metavar='', required=True,
                        help="router telnet address to connect to",
                        default=None)

    parser.add_argument('-p', '--port', metavar='', type=int,
                        help="router telnet port to connect to",
                        default=23)

    parser.add_argument('-u', '--username', metavar='',
                        help="username to authenticate with",
                        default=None)

    parser.add_argument('-x', '--password', metavar='',
                        help="password to authenticate with",
                        default=None)

    parser.add_argument('-t', '--timeout', metavar='', type=int,
                        help="network timeout in milliseconds",
                        default=5000)

    args = parser.parse_args()

    with globals()[args.router](args.host, args.port, args.timeout / 1000,
                                args.username, args.password) as router:
        print(json.dumps({
            'router': router.name(),
            'timestamp': time.time(),
            'data': router.get_all_info()
        }, indent=4, sort_keys=True))

if __name__ == '__main__':
    main()
