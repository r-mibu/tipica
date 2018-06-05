%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
%global tipica_group tipica
%global pysite /usr/lib/python2.7/site-packages

Name:             tipica
Epoch:            1
Version:          0.1.1
Release:          1
Summary:          Tipica

License:          ASL 2.0
URL:              http://not.ready.to.be.public/
Source0:          tipica-%{version}.tar.gz
Source1:          tipica_bc.sh
Source2:          tipica
Source3:          tipica-dhcp.service
Source4:          tipica-http.service
Source5:          dnsmasq.conf
Source6:          nginx.conf
Source7:          tipica.conf


BuildArch:        noarch
BuildRequires:    git
BuildRequires:    python-setuptools
BuildRequires:    python-pbr
BuildRequires:    systemd

Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
Requires:         ipmitool
Requires:         sshpass
Requires:         bash-completion
Requires:         nginx
Requires:         dnsmasq
Requires:         dnsmasq-utils
Requires:         sudo
Requires(pre): /usr/sbin/groupadd, /usr/bin/getent
Requires(postun): /usr/sbin/groupdel
Requires:         python-decorator
Requires:         python-sqlalchemy
Requires:         python-six
Requires:         python-prettytable

# dnsmasq-base amtterm nginx-core

%description
Tipica is a simple tool to manage machines from one server. \
Tipica provides owerablity of machines and OS provisioning through \
command line interface.  You can share machines in your team and \
launching OS easily and quickly.

%prep
%autosetup -n tipica-%{upstream_version} -S git
find . \( -name .gitignore -o -name .placeholder \) -delete
#%py_req_cleanup

%build
python setup.py build

%install
python setup.py install -O1 --skip-build --root %{buildroot}

install -p -D -m 644 %{SOURCE1} %{buildroot}/etc/profile.d/tipica_bc.sh
install -p -D -m 440 %{SOURCE2} %{buildroot}/etc/sudoers.d/tipica

install -d -m 755 %{buildroot}/etc/tipica
install -p -D -m 644 %{SOURCE5} %{buildroot}/etc/tipica/dnsmasq.conf
install -p -D -m 644 %{SOURCE6} %{buildroot}/etc/tipica/nginx.conf
install -p -D -m 644 %{SOURCE7} %{buildroot}/etc/tipica/tipica.conf

install -p -D -m 644 %{SOURCE3} %{buildroot}/usr/lib/systemd/system/tipica-dhcp.service
install -p -D -m 644 %{SOURCE4} %{buildroot}/usr/lib/systemd/system/tipica-http.service

install -d -m 755 %{buildroot}/var/lib/tipica
install -d -m 775 %{buildroot}/var/lib/tipica/db
install -p -D -m 664 /dev/null %{buildroot}/var/lib/tipica/db/db.sqlite3
install -d -m 775 %{buildroot}/var/lib/tipica/dnsmasq
ln -sf /etc/tipica/dnsmasq.conf %{buildroot}/var/lib/tipica/dnsmasq/conf
#install -p -D -m 664 /dev/null %{buildroot}/var/lib/tipica/dnsmasq/images
#install -p -D -m 664 /dev/null %{buildroot}/var/lib/tipica/dnsmasq/nodes
install -d -m 755 %{buildroot}/var/lib/tipica/export

install -d -m 755 %{buildroot}/var/run/tipica

%pre
getent group %{tipica_group} >/dev/null || groupadd %{tipica_group}
exit 0

%post
/usr/bin/tipica db-init
%systemd_post tipica-dhcp.service
%systemd_post tipica-http.service

%preun
%systemd_preun tipica-dhcp.service
%systemd_preun tipica-http.service

%postun
%systemd_postun_with_restart tipica-dhcp.service
%systemd_postun_with_restart tipica-http.service

%files

/etc/profile.d/tipica_bc.sh
/etc/sudoers.d/tipica

%dir /etc/tipica
%config(noreplace) %attr(0644, root, %{tipica_group}) /etc/tipica/dnsmasq.conf
%config(noreplace) %attr(0644, root, %{tipica_group}) /etc/tipica/nginx.conf
%config(noreplace) %attr(0644, root, %{tipica_group}) /etc/tipica/tipica.conf

%dir /var/lib/tipica
%dir %attr(0775, root, %{tipica_group}) /var/lib/tipica/db
%config(noreplace) %attr(0664, root, %{tipica_group}) /var/lib/tipica/db/db.sqlite3
%dir %attr(0775, root, %{tipica_group}) /var/lib/tipica/dnsmasq
/var/lib/tipica/dnsmasq/conf
#%config(noreplace) %attr(0664, root, %{tipica_group}) /var/lib/tipica/dnsmasq/images
#%config(noreplace) %attr(0664, root, %{tipica_group}) /var/lib/tipica/dnsmasq/nodes
%dir /var/lib/tipica/export

%dir /var/run/tipica

/usr/bin/tipica
%{pysite}/tipica
%{pysite}/tipica-*.egg-info
/usr/lib/systemd/system/tipica-dhcp.service
/usr/lib/systemd/system/tipica-http.service

%changelog
