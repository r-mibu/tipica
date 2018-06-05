import os
import pwd
import signal
import six
import subprocess
import sys

import prettytable as pt

import tipica.exceptions as exc


def print_table(fields, rows):
    pt_options = {
        'hrules': pt.HEADER,
        'vrules': pt.NONE,
        'left_padding_width': 1,
        'right_padding_width': 1,
    }
    p = pt.PrettyTable(fields, **pt_options)

    for r in rows:
        p.add_row([r.get(f) or '' for f in fields])

    print p


def decode(text):
    if isinstance(text, six.text_type):
        return text
    elif isinstance(text, six.string_types):
        incoming = (sys.stdin.encoding or sys.getdefaultencoding() or 'utf-8')
        return text.decode(incoming, 'strict')
    else:
        raise TypeError("%s can't be decoded" % type(text))


def get_username():
    return pwd.getpwuid(os.getuid())[0]


def execute(cmd, set_pipe=True, timeout=None, env=None):
    args = {}
    if set_pipe:
        args['stdin'] = subprocess.PIPE
        args['stdout'] = subprocess.PIPE
        args['stderr'] = subprocess.PIPE
    if env:
        args['env'] = env
    p = subprocess.Popen(cmd, **args)

    if timeout:
        def alarm_handler(signum, frame):
            raise exc.TimeoutExpired

        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(timeout)

    try:
        outstr, errstr = p.communicate()
        if timeout:
            signal.alarm(0)
    except exc.TimeoutExpired:
        p.kill()
        raise

    if set_pipe:
        out = outstr.splitlines()
        err = errstr.splitlines()
    else:
        out = []
        err = []
    ret = p.returncode
    return (out, err, ret)


def get_mgmt_hostname(node):
    return "%s-%s" % (node['name'], node['mgmt_type'])


def update_dhcp():
    cmd = ['sudo', '/bin/systemctl', 'restart', 'tipica-dhcp']
    out, err, ret = execute(cmd)
    if ret != 0:
        raise Exception("Failed to update dhcp server config: %s." % err)


def ssh_execute(host, user, password):
    cmd = ['sshpass', '-p', password,
           'ssh', '-o', 'StrictHostKeyChecking=no',
           '-o', 'UserKnownHostsFile=/dev/null',
           '-l', user, host]
    execute(cmd, set_pipe=False)


def add_line(filepath, line):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for l in f:
                if l.rstrip() == line:
                    return True

    with open(filepath, 'a') as f:
        f.write("%s\n" % line)


def edit_line(filepath, startstr, line):
    if not os.path.exists(filepath):
        add_line(filepath, line)
        return

    txt = []
    edited = False
    with open(filepath, 'r') as f:
        for l in f:
            if l.startswith(startstr):
                edited = True
                txt.append("%s\n" % line)
            else:
                txt.append(l)
    if edited:
        with open(filepath, 'w') as f:
            f.writelines(txt)


def delete_line(filepath, startstr):
    if not os.path.exists(filepath):
        return

    txt = []
    deleted = False
    with open(filepath, 'r') as f:
        for l in f:
            if l.startswith(startstr):
                deleted = True
            else:
                txt.append(l)
    if deleted:
        with open(filepath, 'w') as f:
            f.writelines(txt)
