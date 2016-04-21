# -*- coding: utf-8 -*-
#!/usr/bin/python

import logging
import re
import telnetlib

import paramiko


class QuaggaConfig(object):
    current_networks = set()
    def __init__(self):
        self.ssh_host = '10.60.0.114'
        self.ssh_user = 'icmrsu'
        self.ssh_secret = 'gr@peb1ke'
        self.ssh_port = 22
        self.conf_file_path = '/etc/quagga/bgpd.conf'

        # Зададим параметры логгирования
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        file_handler = logging.FileHandler('dns-sniffer.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def read_current_networks(self):
        """
        Получаем уже заданные IP адреса  сетей из файла конфигурации Quagga
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.ssh_host, username=self.ssh_user, password=self.ssh_secret, port=self.ssh_port)
        sftp = client.open_sftp()

        # Считываем из файла конфигурации имеюшиеся сети
        with sftp.open(self.conf_file_path, 'r') as f:
            for line in f:
                network_line = re.findall('network\s+(\d+\D\d+\D\d+\D\d+)/(\d+)', line)
                if network_line:
                    net = network_line[0][0]
                    pfx = network_line[0][1]
                    self.current_networks.add(net)
        self.logger.info('From Quagga conf file loaded %s networks' % len(self.current_networks))
        return self.current_networks

    def telnet_call(self):
        # Подключаемся к виртуальному маршрутизатору
        quagga_host = '10.60.0.114'
        quagga_port = '2605'
        quagga_password = r'gr@peb1ke'
        telnet = telnetlib.Telnet(quagga_host, quagga_port, 3)
        telnet.read_until('Password: ', 3)
        telnet.write(quagga_password + '\r\n')
        telnet.expect([re.compile('.*>\s'), ], 3)
        telnet.write('en' + '\r\n')
        telnet.read_until('Password: ', 3)
        telnet.write(quagga_password + '\r\n')
        telnet.expect([re.compile('.*#\s'), ], 3)
        telnet.write('term len 0' + '\r\n')
        # Сложно объяснить почему, но здесь нужны две команды
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        return telnet

    def add_bgp_networks(self, set_of_networks):
        """

        :param set_of_networks: Множество IP адресов, которые необхордимо занести в конфигурацию BGP
        """
        net_mask = '32'
        telnet = self.telnet_call()
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        telnet.write("conf t\r")
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        telnet.write("router bgp 8941\r\n")
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        for network in set_of_networks:
            telnet.write("network " + network + "/" + net_mask + "\r")
            self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 10))
            self.logger.info("added to quagga bgp network %s/%s" % (network, net_mask))
        telnet.write('end\r')
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        telnet.write('write' + '\r')
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        telnet.write('exit' + '\r\n')
        telnet.close()

    def delete_bgp_networks(self, set_of_networks):
        net_mask = '32'
        telnet = self.telnet_call()
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        telnet.write("conf t\r")
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        telnet.write("router bgp 8941\r\n")
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        for network in set_of_networks:
            telnet.write("no network " + network + "/" + net_mask + "\r")
            self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 10))
            self.logger.info('deleted from quagga bgp network %s/%s' % (network, net_mask))
        telnet.write("end\r")
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        telnet.write("write\r")
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        self.logger.debug(telnet.expect([re.compile('.*#\s'), ], 3))
        telnet.write('exit' + '\r\n')
        telnet.close()



q = QuaggaConfig()
#q.read_current_networks()
#q.add_bgp_networks({'0.1.1.1', '0.1.1.3'})
q.delete_bgp_networks({'0.1.1.1', '0.1.1.2'})