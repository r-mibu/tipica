import sys


DEFAULT = 'tipica.drivers.ipmitool.IPMIToolDriver'
DRIVERS = {'amt': 'tipica.drivers.amtterm.AMTTermDriver'}


def import_class(import_str):
    mod_str, _sep, class_str = import_str.rpartition('.')
    __import__(mod_str)
    try:
        return getattr(sys.modules[mod_str], class_str)
    except AttributeError:
        raise ImportError('Class %s cannot be found (%s)' %
                          (class_str,
                           traceback.format_exception(*sys.exc_info())))


def get(node):
    driver_klass = DRIVERS.get(node['mgmt_type'], DEFAULT)
    return import_class(driver_klass)(node)
