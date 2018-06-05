
TIPICA_GROUP := tipica
TIPICA_VERSION := $$(git describe --abbrev=0)
TIPICA_BUILD := $(PWD)/rpmbuild
TIPICA_SOURCE := ${TIPICA_BUILD}/SOURCES


.PHONY : check clean install uninstall update install_files rpm

rpm:
	grep "CentOS Linux release 7" /etc/redhat-release || exit 3
	which rpmbuild || exit 4
	#sudo yum -y install rpm-build rpmdevtools make gcc git python-setuptools python-pbr
	rm -rf ${TIPICA_BUILD}
	mkdir -p ${TIPICA_BUILD}/{BUILD,RPMS,SOURCES}
	git archive --prefix=tipica-0.1.1/ -o ${TIPICA_SOURCE}/tipica-0.1.1.tar.gz 0.1.1
	cp etc/profile.d/tipica_bc.sh \
	    etc/sudoers.d/tipica \
	    etc/systemd/system/tipica-dhcp.service \
	    etc/systemd/system/tipica-http.service \
	    etc/tipica/dnsmasq.conf \
	    etc/tipica/nginx.conf \
	    etc/tipica/tipica.conf \
	    ${TIPICA_SOURCE}/
	rpmbuild -bb --define "_topdir ${TIPICA_BUILD}" tipica.spec

check:
	whoami | grep -q "^root$$" || exit 1
	lsb_release -d | grep -q "Ubuntu 16.04" || exit 2

clean:
	rm -f AUTHORS ChangeLog
	rm -rf build tipica.egg-info
	rm -rf rpmbuild

install: install_files
	# group
	groupadd -f $(TIPICA_GROUP)
	# systemd
	systemctl daemon-reload
	systemctl enable tipica-http
	systemctl enable tipica-dhcp
	# etc
	install -pd /etc/tipica/
	install -pm 644 etc/tipica/dnsmasq.conf /etc/tipica/dnsmasq.conf
	install -pm 644 etc/tipica/nginx.conf /etc/tipica/nginx.conf
	install -pm 644 etc/tipica/tipica.conf /etc/tipica/tipica.conf
	# var
	install -pm 775 -g $(TIPICA_GROUP) -d /var/lib/tipica/db
	install -m 664 -g $(TIPICA_GROUP) /dev/null /var/lib/tipica/db/db.sqlite3
	install -pm 775 -g $(TIPICA_GROUP) -d /var/lib/tipica/dnsmasq
	ln -sf /etc/tipica/dnsmasq.conf /var/lib/tipica/dnsmasq/conf
	install -m 664 -g $(TIPICA_GROUP) /dev/null /var/lib/tipica/dnsmasq/images
	install -m 664 -g $(TIPICA_GROUP) /dev/null /var/lib/tipica/dnsmasq/nodes
	install -pd /var/lib/tipica/export
	install -pd /var/run/tipica
	# service
	/usr/local/bin/tipica db-init
	systemctl restart tipica-http
	systemctl restart tipica-dhcp

install_files: check
	# python
	pip install -U -r requirements.txt
	python setup.py install
	# bash_completion
	install -pm 644 etc/profile.d/tipica_bc.sh /etc/profile.d/tipica_bc.sh
	# sudoers
	install -pm 440 etc/sudoers.d/tipica /etc/sudoers.d/tipica
	# systemd
	install -pm 644 etc/systemd/system/tipica-dhcp.service /etc/systemd/system/tipica-dhcp.service
	install -pm 644 etc/systemd/system/tipica-http.service /etc/systemd/system/tipica-http.service

uninstall: check
	# service
	systemctl stop tipica-http || :
	systemctl stop tipica-dhcp || :
	# var
	rm -rf /var/lib/tipica
	# etc
	rm -rf /etc/tipica
	# systemd
	systemctl disable tipica-http || :
	systemctl disable tipica-dhcp || :
	rm -f /etc/systemd/system/tipica-dhcp.service
	rm -f /etc/systemd/system/tipica-http.service
	systemctl daemon-reload
	# sudoers
	rm -f /etc/sudoers.d/tipica
	# bash_completion
	rm -f /etc/profile.d/tipica_bc.sh
	# group won't be removed
	# python
	rm -rf /usr/local/lib/python2.7/dist-packages/tipica*
	rm -f /usr/local/bin/tipica

update: install_files
	# service
	systemctl daemon-reload
	systemctl restart tipica-dhcp
	systemctl restart tipica-http
