import os
import random
import re
import shutil
import string
import urllib

from tipica import config
from tipica import utils


TMP_DIR = '/tmp/tipica'
PXECONF_TEMPLATE = '''
default linux
label linux
kernel %(kernel)s
append initrd=%(initrd)s %(param)s console=tty0 console=ttyS1,115200n8 edd=off
IPAPPEND 2
'''
KICKSTART_TEMPLATE = '''
auth --enableshadow --passalgo=sha512
url --url=%(repo)s
text
firstboot --enable
ignoredisk --only-use=sda
keyboard --vckeymap=us --xlayouts='us'
lang en_US.UTF-8
network  --bootproto=dhcp --device=bootif --ipv6=auto --activate
network  --hostname=localhost.localdomain
rootpw --plaintext --lock %(root_pw)s
services --enabled="chronyd"
skipx
reboot
timezone %(tz)s --isUtc --ntpservers=%(ntp_servers)s
user --groups=wheel --name=%(user_name)s --password=%(user_pw)s --plaintext --gecos="%(user_name)s"
bootloader --append=" crashkernel=auto" --location=mbr --boot-drive=sda
autopart --type=lvm
clearpart --all --initlabel --drives=sda
%%packages
@core
chrony
kexec-tools
%%end
%%post
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.orig
sed -i -e 's/^UseDNS/#UseDNS/' /etc/ssh/sshd_config
echo 'UseDNS no' >>/etc/ssh/sshd_config
echo '%(user_name)s ALL=(ALL:ALL) NOPASSWD: ALL' > /etc/sudoers.d/%(user_name)s
%%end
'''
PRESEED_TEMPLATE = '''
## https://help.ubuntu.com/lts/installation-guide/example-preseed.txt
d-i mirror/country string JP
d-i mirror/http/mirror select jp.archive.ubuntu.com
d-i mirror/http/proxy select
d-i passwd/make-user boolean true
d-i passwd/user-fullname string %(user_name)s
d-i passwd/username string %(user_name)s
d-i passwd/user-password password %(user_pw)s
d-i passwd/user-password-again password %(user_pw)s
d-i user-setup/allow-password-weak boolean true
d-i user-setup/encrypt-home boolean false
d-i clock-setup/utc boolean true
d-i time/zone string %(tz)s
d-i clock-setup/ntp boolean true
d-i clock-setup/ntp-server string %(ntp_servers)s
d-i partman-auto/disk string /dev/[sv]da
d-i partman-auto/method string lvm
d-i partman-lvm/device_remove_lvm boolean true
d-i partman-lvm/confirm boolean true
d-i partman-lvm/confirm_nooverwrite boolean true
d-i partman-auto-lvm/guided_size string max
d-i partman-auto/choose_recipe select atomic
d-i partman-md/device_remove_md boolean true
d-i partman-partitioning/confirm_write_new_label boolean true
d-i partman/choose_partition select finish
d-i partman/confirm boolean true
d-i partman/confirm_nooverwrite boolean true
tasksel tasksel/first multiselect none
d-i pkgsel/include string openssh-server
d-i pkgsel/upgrade select none
d-i pkgsel/update-policy select none
popularity-contest popularity-contest/participate boolean false
d-i pkgsel/updatedb boolean false
d-i grub-installer/only_debian boolean true
#grub-installer  grub-installer/choose_bootdev   select  /dev/sda
d-i finish-install/reboot_in_progress note
d-i preseed/late_command string cp /target/etc/ssh/sshd_config{,.orig}; sed -i -e 's/^UseDNS/#UseDNS/' -e '$ a UseDNS no' /target/etc/ssh/sshd_config; echo '%(user_name)s ALL=(ALL:ALL) NOPASSWD: ALL' > /target/etc/sudoers.d/%(user_name)s; in-target /bin/systemctl enable getty@ttyS1.service
'''


def check_support(name):
    if name not in BUILDERS:
        raise Exception("Image name <%s> is not supported" % name)


def generate_pw(n=16):
    return ''.join([random.choice(string.ascii_letters + string.digits) for i in range(n)])


def generate_pxeconf(image_dir, kernel, initrd, param):
    data = PXECONF_TEMPLATE % {'kernel': kernel, 'initrd': initrd, 'param': param}
    pxeconf_dir = os.path.join(image_dir, 'pxelinux.cfg')
    os.makedirs(pxeconf_dir)
    pxeconf = os.path.join(pxeconf_dir, 'default')
    with open(pxeconf, 'w') as f:
        f.write(data)


def make_image_dir(conf, name):
    image_dir = os.path.join(conf['export_dir'], name)
    if os.path.exists(image_dir):
        raise Exception("Image <%s> already exists in %s" % (name, image_dir))
    os.makedirs(image_dir)
    return image_dir


def clear_tmp():
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
    os.makedirs(TMP_DIR)


def download_cent7_pxelinux(conf, image_dir):
    clear_tmp()
    packages_url = '%s/Packages/' % conf['image_cent7_repo']
    packages_list = os.path.join(TMP_DIR, 'pkgs')
    urllib.urlretrieve(packages_url, packages_list)
    with open(packages_list, 'r') as f:
        match = re.search('>syslinux-[0-9].*.rpm<', f.read())
        syslinux_rpm = match.group().strip('<>')
    syslinux_url = '%s/%s' % (packages_url, syslinux_rpm)
    urllib.urlretrieve(syslinux_url, os.path.join(TMP_DIR, 'syslinux.rpm'))
    unpack_cmd = '''
    #!/bin/bash
    cd %(dir)s
    rpm2cpio %(dir)s/syslinux.rpm | cpio -imd ./usr/share/syslinux/pxelinux.0
    mv ./usr/share/syslinux/pxelinux.0 .
    ''' % {'dir': TMP_DIR}
    unpack_shell = os.path.join(TMP_DIR, 'unpack.sh')
    with open(unpack_shell, 'w') as f:
        f.write(unpack_cmd)
    utils.execute(['/bin/bash', unpack_shell])
    os.rename(os.path.join(TMP_DIR, 'pxelinux.0'),
              os.path.join(image_dir, 'pxelinux.0'))


def cent7_build(conf, name):
    image_dir = make_image_dir(conf, name)

    base_url = '%s/images/pxeboot' % conf['image_cent7_repo']
    for f in ('initrd.img', 'vmlinuz'):
        urllib.urlretrieve('%s/%s' % (base_url, f), os.path.join(image_dir, f))
    download_cent7_pxelinux(conf, image_dir)

    user_pw = generate_pw()
    ks_conf = KICKSTART_TEMPLATE % {
        'ntp_servers': conf['image_ntp_servers'],
        'repo': conf['image_cent7_repo'],
        'root_pw': generate_pw(),
        'user_name': conf['image_user_name'],
        'user_pw': user_pw,
        'tz': conf['image_timezone'],
    }
    with open(os.path.join(image_dir, 'ks'),'w') as f:
        f.write(ks_conf)

    params = [
        'inst.repo=%s' % conf['image_cent7_repo'],
        'ks=%s/%s/ks' % (conf['image_http_server'], name)
    ]
    generate_pxeconf(image_dir, 'vmlinuz', 'initrd.img', ' '.join(params))

    print "Done! Register this image as follows:"
    print "    tipica image-add %(name)s %(user)s %(pw)s '%(desc)s'" % {
        'name': name, 'user': conf['image_user_name'], 'pw': user_pw,
        'desc': 'CentOS 7.x network installer',
    }


def xenial_build(conf, name):
    image_dir = make_image_dir(conf, name)

    base_url = '%s/%s' % (conf['image_xenial_repo'],
        'installer-amd64/current/images/netboot/ubuntu-installer/amd64')
    for f in ('initrd.gz', 'linux', 'pxelinux.0', 'boot-screens/ldlinux.c32'):
        urllib.urlretrieve('%s/%s' % (base_url, f),
                           os.path.join(image_dir, os.path.basename(f)))

    user_pw = generate_pw()
    ps_conf = PRESEED_TEMPLATE % {
        'ntp_servers': conf['image_ntp_servers'],
        'user_name': conf['image_user_name'],
        'user_pw': user_pw,
        'tz': conf['image_timezone'],
    }
    with open(os.path.join(image_dir, 'preseed'),'w') as f:
        f.write(ps_conf)

    params = [
        'text', 'auto', 'interface=auto', 'locale=en_US', 'keymap=us',
        'hostname=', 'url=%s/%s/preseed' % (conf['image_http_server'], name)
    ]
    generate_pxeconf(image_dir, 'linux', 'initrd.gz', ' '.join(params))

    print "Done! Register this image as follows:"
    print "    tipica image-add %(name)s %(user)s %(pw)s '%(desc)s'" % {
        'name': name, 'user': conf['image_user_name'], 'pw': user_pw,
        'desc': 'Ubuntu 16.04 (xenial) network installer',
    }


BUILDERS = {
    'cent7': cent7_build,
    'xenial': xenial_build,
}


def build(name):
    check_support(name)
    builder = BUILDERS.get(name)
    builder(config.CFG, name)
