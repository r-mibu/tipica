import tipica.exceptions as exc
import tipica.utils as utils


POWER_STATUS = 'Chassis Power is'
POWER_STATUS_MAP = {'Chassis Power is on': 'on',
                    'Chassis Power is off': 'off'}
TIMEOUT = 1


class IPMIToolDriver(object):

    def __init__(self, node):
        self.hostname = utils.get_mgmt_hostname(node)
        self.account = node['mgmt_account']
        self.passwd = node['mgmt_password']

    def _ipmi_request(self, ipmi_cmd, set_pipe=True, timeout=None):
        cmd = ['ipmitool', '-I', 'lanplus',
               '-H', self.hostname, '-U', self.account, '-P', self.passwd]
        cmd += ipmi_cmd.split()
        out, err, ret = utils.execute(cmd, set_pipe=set_pipe, timeout=timeout)
        if ret != 0:
            msg = "node=%s .\n    " % self.hostname
            msg += '\n    '.join(err)
            raise exc.DriverFailed(err=msg)
        return out

    def status(self):
        try:
            out = self._ipmi_request("power status", timeout=TIMEOUT)
        except exc.TimeoutExpired:
            return '(timeout)'

        for l in out:
            if l.startswith(POWER_STATUS):
                return POWER_STATUS_MAP.get(l.strip(), '(unkown)')
        return '(unkown)'

    def start(self):
        self._ipmi_request("power on")

    def pxeboot(self):
        self._ipmi_request("chassis bootdev pxe")
        self.start()

    def console(self):
        self._ipmi_request("-e = sol activate", set_pipe=False)

    def shutdown(self):
        self._ipmi_request("power soft")

    def destroy(self):
        self._ipmi_request("power off")
