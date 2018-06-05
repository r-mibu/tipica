import json

from tipica import db
from tipica import config
from tipica import drivers
from tipica import exceptions
from tipica import utils


class ObjectBase(object):

    @classmethod
    def _resource_name(cls):
        return cls.__name__.lower()

    @classmethod
    def add(cls, *argv):
        if len(cls.creation_params) != len(argv):
            raise Exception("Bad request, arg must be: <%s>." %
                            '> <'.join(cls.creation_params))
        params = dict(zip(cls.creation_params, argv))
        entry = db.add(cls._resource_name(), **params)
        print ("%(r)s %(n)s successfully created." %
               {'r': cls.__name__, 'n': entry['name']})

    @classmethod
    def update(cls, name, *argv):
        params = {}
        for arg in argv:
            key, value = arg.split('=')
            if key not in cls.creation_params:
                raise Exception("Bad request, available args are: <%s>." %
                                '> <'.join(cls.creation_params))
            params[key] = value
        entry = db.update(cls._resource_name(), name, **params)
        print ("%(r)s %(n)s successfully updated." %
               {'r': cls.__name__, 'n': entry['name']})

    @classmethod
    def list(cls, filters=None, fields=None):
        f = {}
        if filters and not isinstance(filters, dict):
            try:
                f = json.loads(filters)
            except Exception:
                raise Exception("Bad request, invalid filters description.")

        f, r = db.table(cls._resource_name(), filters=f)
        utils.print_table(fields or f, r)

    @classmethod
    def names(cls):
        f, r = db.table(cls._resource_name())
        print ' '.join([i['name'] for i in r])

    @classmethod
    def delete(cls, name):
        db.delete(cls._resource_name(), name)
        print ("%(r)s %(n)s successfully deleted." %
               {'r': cls.__name__, 'n': name})


class User(ObjectBase):
    creation_params = ['name']


class Image(ObjectBase):
    creation_params = ['name', 'user_name', 'user_pass', 'description']
    conf = config.CFG['dnsmasq_image']

    @classmethod
    def _dnsmasq_line(cls, image_name):
        return "dhcp-boot=tag:%(i)s,%(i)s/pxelinux.0" % {'i': image_name}

    @classmethod
    def add(cls, *argv):
        super(cls, Image).add(*argv)
        utils.add_line(cls.conf, cls._dnsmasq_line(argv[0]))
        utils.update_dhcp()

    @classmethod
    def delete(cls, name):
        super(cls, Image).delete(name)
        utils.delete_line(cls.conf, cls._dnsmasq_line(name))
        utils.update_dhcp()

    @classmethod
    def list_for_user(cls):
        super(cls, Image).list(fields=['name', 'description'])


class Node(ObjectBase):
    creation_params = ['name', 'mgmt_type', 'mgmt_account', 'mgmt_password']
    conf = config.CFG['dnsmasq_node']

    @classmethod
    def _dnsmasq_line(cls, node_name, image_name=None):
        if not image_name:
            return "dhcp-host=%(n)s," % {'n': node_name}
        return "dhcp-host=%(n)s,set:%(i)s" % {'n': node_name, 'i': image_name}

    @classmethod
    def add(cls, *argv):
        super(cls, Node).add(*argv)
        utils.add_line(cls.conf, cls._dnsmasq_line(argv[0]))
        utils.update_dhcp()

    @classmethod
    def delete(cls, name):
        super(cls, Node).delete(name)
        utils.delete_line(cls.conf, cls._dnsmasq_line(name))
        utils.update_dhcp()

    @classmethod
    def _check_permission(cls, name):
        user = utils.get_username()
        node = db.get(cls._resource_name(), name)
        if user not in (node['user'], 'root'):
            raise Exception("You don't have permission.")
        return node

    @classmethod
    def status(cls, name=None):
        fields = ['name', 'power', 'image', 'user', 'description']
        if name:
            nodes = [db.get(cls._resource_name(), name)]
        else:
            nodes = db.list(cls._resource_name())
            nodes.sort(key=lambda node: node['name'])

        for node in nodes:
            try:
                node['power'] = drivers.get(node).status()
            except exceptions.DriverFailed:
                node['power'] = '(unkown)'
        utils.print_table(fields, nodes)

    @classmethod
    def acquire(cls, name):
        user = utils.get_username()
        node = db.get(cls._resource_name(), name)
        if node['user']:
            raise Exception("Node %s is occupied." % name)
        db.update(cls._resource_name(), name, user=user)

    @classmethod
    def set_user(cls, name, username=None):
        cls._check_permission(name)
        db.update(cls._resource_name(), name, user=username)

    @classmethod
    def release(cls, name):
        cls._check_permission(name)
        node = db.update('node', name, user=None, image=None, description=None)
        # TODO: update dnsmasq config
        drivers.get(node).destroy()
        utils.edit_line(cls.conf, cls._dnsmasq_line(name),
                        cls._dnsmasq_line(name))
        utils.update_dhcp()

    @classmethod
    def start(cls, name):
        cls._check_permission(name)
        node = db.get(cls._resource_name(), name)
        drivers.get(node).start()

    @classmethod
    def pxeboot(cls, name, image_name):
        cls._check_permission(name)

        node = db.update(cls._resource_name(), name, image=image_name)
        utils.edit_line(cls.conf, cls._dnsmasq_line(name),
                        cls._dnsmasq_line(name, image_name))
        utils.update_dhcp()

        drivers.get(node).pxeboot()

    @classmethod
    def shutdown(cls, name):
        cls._check_permission(name)
        node = db.get(cls._resource_name(), name)
        drivers.get(node).shutdown()

    @classmethod
    def destroy(cls, name):
        cls._check_permission(name)
        node = db.get(cls._resource_name(), name)
        drivers.get(node).destroy()

    @classmethod
    def set_image(cls, name, image_name):
        cls._check_permission(name)
        db.update(cls._resource_name(), name, image=image_name)
        utils.edit_line(cls.conf, cls._dnsmasq_line(name),
                        cls._dnsmasq_line(name, image_name))
        utils.update_dhcp()

    @classmethod
    def login(cls, name):
        node = cls._check_permission(name)
        if not node['image']:
            raise Exception("Node %s has no image." % node['name'])
        utils.ssh_execute(node['name'], node['image_ref']['user_name'],
                          node['image_ref']['user_pass'])

    @classmethod
    def console(cls, name):
        node = cls._check_permission(name)
        drivers.get(node).console()

    @classmethod
    def note(cls, name, description=''):
        cls._check_permission(name)
        db.update(cls._resource_name(), name, description=description)

    @classmethod
    def names_owned(cls):
        user = utils.get_username()
        f, r = db.table(cls._resource_name(), filters={'user': user})
        print ' '.join([i['name'] for i in r])

    @classmethod
    def names_free(cls):
        f, r = db.table(cls._resource_name(), filters={'user': None})
        print ' '.join([i['name'] for i in r])
