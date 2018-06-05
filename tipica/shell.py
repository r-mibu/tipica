import sys
import os

import tipica
from tipica import config
from tipica import db
from tipica import image_builder
from tipica import objects
from tipica import utils


TIPICA_ADMIN = 'root'


def validate_user(username):
    try:
        db.get('user', username)
    except:
        raise Exception("User %s cannot use tipica." % username)


class ShellBase(object):

    commands = {}
    default_command = 'usage'
    usage = ':-p'

    def get_command(self, argv):
        if len(argv) == 0:
            cmd_str = self.default_command
        else:
            cmd_str = argv[0]
        if cmd_str == 'version':
            return tipica.__version__
        if cmd_str in ('--help', 'help', 'usage'):
            return self.usage
        try:
            return self.commands[cmd_str]
        except KeyError:
            raise Exception("%s is not a tipica command. "
                            "See 'tipica usage'." % cmd_str)

    def execute(self, cmd, argv):
        if not callable(cmd):
            print cmd
            return
        if len(argv) > 1:
            cmd(*argv[1:])
        else:
            cmd()

    def main(self, user, argv):
        config.parse()
        cmd = self.get_command(argv)
        self.execute(cmd, argv)


class TipicaShell(ShellBase):

    usage = """
Usage: tipica <command> ...

Commands:
    status [node]              show current machine(s) status (default)

    acquire <node>             get your own machine
    switch <node> <user>       pass ownership to another user
    release <node>             destroy and release your machine

    pxeboot <node> <image>     boot your machine with an image by PXE
    start <node>               power on your machine (boot from default device)
    shutdown <node>            send ACPI shutdown signal to your machine
    destroy <node>             power off your machine

    images                     list available images

    login <node>               login to your machine with ssh
    console <node>             connect to your machine with serial console
                               ('=.' to exit)
    note <node> [description]  write description of your machine
"""
#   version
    commands = {
        'status': objects.Node.status,
        'acquire': objects.Node.acquire,
        'switch': objects.Node.set_user,
        'release': objects.Node.release,
        'start': objects.Node.start,
        'pxeboot': objects.Node.pxeboot,
        'shutdown': objects.Node.shutdown,
        'destroy': objects.Node.destroy,
        'images': objects.Image.list_for_user,
        'login': objects.Node.login,
        'console': objects.Node.console,
        'note': objects.Node.note,

        # for bash completion
        'node-names-owned': objects.Node.names_owned,
        'node-names-free': objects.Node.names_free,
        'image-names': objects.Image.names,
        'user-names': objects.User.names,
    }
    default_command = 'status'


class TipicaAdminShell(ShellBase):

    usage = """
Usage: tipica
       tipica <command> ...

This is admin command to create entries of Node, Image and User into tipica.

Commands:
    status
    db-init

    node-list
    node-add <node_name> <mgmt_type> <mgmt_account> <mgmt_password>
    node-update <node_name> <key>=<value>
    node-delete <node_name>
    set-user <node_name> <user_name>
    set-image <node_name> <image_name>

    user-list
    user-add <user_name>
    user-update <user_name> <key>=<value>
    user-delete <user_name>

    image-list
    image-add <image_name> <account_name> <account_password> <description>
    image-update <image_name> <key>=<value>
    image-delete <image_name>

    image-build <image_name>   **experimental: 'cent7', 'xenial'**
"""
    commands = {
        'db-init': db.initialize,
        'status': objects.Node.status,
        'node-list': objects.Node.list,
        'node-add': objects.Node.add,
        'node-update': objects.Node.update,
        'node-delete': objects.Node.delete,
        'set-user': objects.Node.set_user,
        'set-image': objects.Node.set_image,
        'user-list': objects.User.list,
        'user-add': objects.User.add,
        'user-update': objects.User.update,
        'user-delete': objects.User.delete,
        'image-list': objects.Image.list,
        'image-add': objects.Image.add,
        'image-update': objects.Image.update,
        'image-delete': objects.Image.delete,
        'image-build': image_builder.build,

        # for bash completion
        'node-names': objects.Node.names,
        'image-names': objects.Image.names,
        'user-names': objects.User.names,
    }
    default_command = 'status'


def main():
    user = utils.get_username()
    if user == TIPICA_ADMIN:
        shell = TipicaAdminShell()
    else:
        validate_user(user)
        shell = TipicaShell()

    try:
        shell.main(user, map(utils.decode, sys.argv[1:]))
    except Exception as e:
        if os.environ.get('TIPICA_DEBUG'):
            raise
        sys.stderr.write("tipica: %s\n" % str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
