CONFIG_FILE = '/etc/tipica/tipica.conf'
CFG = {
    'sql_connection': 'sqlite:////var/lib/tipica/db/db.sqlite3',
    'dnsmasq_conf': "/var/lib/tipica/dnsmasq/conf",
    'dnsmasq_image': "/var/lib/tipica/dnsmasq/images",
    'dnsmasq_node': "/var/lib/tipica/dnsmasq/nodes",
    'export_dir': "/var/lib/tipica/export",
    'image_cent7_repo': "http://ftp.riken.jp/Linux/centos/7/os/x86_64",
    'image_xenial_repo': "http://ftp.riken.jp/Linux/ubuntu/dists/xenial/main",
    'image_http_server': "http://192.168.1.1:9999",
    'image_ntp_servers': "192.168.1.1",
    'image_user_name': "tipica",
    'image_timezone': "Asia/Tokyo",
}


class ParseError(Exception):

    def __init__(self, message, lineno, line):
        self.msg = message
        self.line = line
        self.lineno = lineno

    def __str__(self):
        return 'at line %d, %s: %r' % (self.lineno, self.msg, self.line)


def parse(config_file=CONFIG_FILE):
    global CFG

    with open(config_file) as f:
        lineno = 0
        for line in f:
            lineno += 1
            line = line.strip()
            if len(line) < 3:
                continue
            if line[0] == '#':
                continue
            equal = line.find('=')
            if equal < 0:
                raise ParseError("No '=' found in assignment", lineno, line)
            key, value = line[:equal].strip(), line[equal + 1:].strip()
            if not key:
                raise ParseError("Key cannot empty", lineno, line)
            if key not in CFG:
                raise ParseError("Unkown key", lineno, line)
            CFG[key] = value
