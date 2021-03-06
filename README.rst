What is tipica?
===============

``tipica`` is a simple tool to manage machines from one server.
``tipica`` provides owerablity of machines and OS provisioning through
command line interface.  You can share machines in your team and launching OS
easily and quickly.

WARN: The owerablity provided by this tool is intended to prevent operation
miss such as logging into wrong machine.  This is not secure enough to lock out
other users from your machine due to the following reasons:

* Network is not isolated.
* OS images are shared, and no passwd/key insertion.
* IP address, MAC address and IPMI password are visible to all users.


Models
======

There are three models in tipica; Node (== machine), Image and User.
Administrator 'root' can register all models.
Tipica users can acquire a free node and operate owned nodes;
available operations are power management, boot with selected image,
ssh login and serial console access.::

        +--------+ 0..1      * +--------+ *      0..1 +---------+
        |  User  | <---------> |  Node  | <---------> |  Image  |
        +--------+             +--------+             +---------+


How to use?
===========

Show all machines and their state as follows.::

        $ tipica

Find an available machine in the list, and acquire it.::

        $ tipica acquire machine01

Boot your machine and launch OS.::

        $ tipica pxeboot machine01 trusty

Wait some minutes to complete boot sequence.  Then, login your machine.::

        $ tipica login machine01

If you want to know what happen in your machine, use serial console
(type '=.' to exit)::

        $ tipica console machine01


How to provide?
===============

1. Connect machines within a local network under master/gateway/jump node.

   NOTE: Make sure that management ports of machines are reachable from the
   master node.

2. Install tipica into the master node::

        (CentOS)
        # yum -y install rpm-build rpmdevtools make gcc git \
                         python-setuptools python-pbr
        # cd /path/to/tipica
        # make rpm

        (Ubuntu)
        # apt update
        # apt -y install python-setuptools python-pip sshpass \
                         ipmitool dnsmasq-base amtterm nginx-core
        # cd /path/to/tipica
        # make install

3. Register Node::

        # vi /etc/hosts 
        # vi /etc/ethers 
        # tipica node-add <node_name> <mgmt_type> <mgmt_account> <mgmt_password>

   NOTE: When you added a new node, add host entries into ``/etc/hosts`` and
   ``/etc/ethers``, corresponding to a pxebootable nic and the management port
   of that node.  Since tipica does not provide IP address management, you have
   to set IP and MAC of those ports for tipica service.
   A hostname of a management port must be "<node name>-<management system>".
   Use 'amt' as <management system> for Intel AMT Node which make tipica
   controll the node via amtterm/amttool.  A node which is used other string in
   <management system> will be controlled via ipmitool.

4. Register User::

        # adduser <user_name>
        # usermod -aG tipica <user_name>
        # tipica user-add <user_name>

   NOTE: unix user entry on the master node is needed to provide tipica access.

5. Register Image::

        # tipica image-build <image_name>
        # tipica image-add <image_name> <account_name> <account_password> <description>

   NOTE: When you build a new image with ``image-build`` command, files for PXE
   boot will be stored into '/var/lib/tipica/export/<image name>/'.

   NOTE: Files under '/var/lib/tipica/export/' will be exposed by HTTP and TFTP
   servers in the master node.


Faster?
=======

You can make a image deployment faster by the followings:

* Configure BIOS options not to run tests or disk initialization.
* Build packege repository to get downloads faster.
* Create small and uncompressed image.
