import os
import requests

import tipica.exceptions as exc
import tipica.utils as utils


POWER_STATUS = 'Powerstate:'
POWER_STATUS_MAP = {'Powerstate:   S0': 'on',
                    'Powerstate:   S5 (soft-off)': 'off'}
TIMEOUT = 1

USE_SOAP_DIRECT = True
POWER_STATE_REQ_DATA = '''
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope \
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
    xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" \
    xmlns:xsd="http://www.w3.org/2001/XMLSchema" \
    soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" \
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <GetSystemPowerState \
            xmlns="http://schemas.intel.com/platform/client/RemoteControl/2004/01" \
            xsi:nil="true" />
    </soap:Body>
</soap:Envelope>
'''
POWER_STATE_REQ_HEADER = {
    'SOAPAction': "http://schemas.intel.com/platform/client/RemoteControl/2004/01#GetSystemPowerState"
}


class AMTTermDriver(object):

    def __init__(self, node):
        self.hostname = node['name']
        self.account = node['mgmt_account']
        self.passwd = node['mgmt_password']

    def _amttool_request(self, amt_cmd, timeout=None):
        # NOTE: amttool have no option to set user account.
        cmd = ['echo', '"y"', '|', 'amttool', self.hostname]
        cmd += amt_cmd.split()
        env = os.environ.copy()
        env['AMT_PASSWORD'] = self.passwd
        out, err, ret = utils.execute(cmd, set_pipe=True,
                                      timeout=timeout, env=env)
        if ret != 0:
            msg = "node=%s .\n    " % self.hostname
            msg += '\n    '.join(err)
            raise exc.DriverFailed(err=msg)
        return out

    def _amtterm_request(self):
        cmd = ['amtterm', '-u', self.account, '-p', self.passwd, self.hostname]
        out, err, ret = utils.execute(cmd, set_pipe=False)
        if ret != 0:
            raise exc.DriverFailed(err='\n    '.join(err))
        return out

    def _status_amttool(self):
        try:
            out = self._amttool_request("info", timeout=TIMEOUT)
        except exc.TimeoutExpired:
            return '(timeout)'

        for l in out:
            if l.startswith(POWER_STATUS):
                return POWER_STATUS_MAP.get(l.rstrip(), '(unkown2)')
        return '(unkown1)'

    def _status_soap_direct(self):
        url = "http://%s:16992/RemoteControlService" % self.hostname
        auth = requests.auth.HTTPDigestAuth(self.account, self.passwd)
        try:
            r = requests.post(url,
                              data=POWER_STATE_REQ_DATA,
                              headers=POWER_STATE_REQ_HEADER,
                              timeout=TIMEOUT,
                              auth=auth,
                              proxies={'http':''})
        except requests.exceptions.Timeout:
            return '(timeout)'

        if r.text.find('<b:SystemPowerState>5</b:SystemPowerState>') >= 0:
            return 'off'
        elif r.text.find('<b:SystemPowerState>0</b:SystemPowerState>') >= 0:
            return 'on'
        else:
            return '(unkown)'

    def status(self):
        if USE_SOAP_DIRECT:
            return self._status_soap_direct()
        else:
            return self._status_amttool()

    def start(self):
        self._amttool_request("powerup")

    def pxeboot(self):
        self._amttool_request("powerup pxe")

    def console(self):
        self._amtterm_request()

    def shutdown(self):
        raise exc.DriverNotSupported(driver='AMT',
                                     command="shutdown (soft-off)")

    def destroy(self):
        self._amttool_request("powerdown")
