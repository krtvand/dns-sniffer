# -*- coding: utf-8 -*-
#!/usr/bin/python

import paramiko
import re
import telnetlib
import logging

class QuaggaConfig(object):
    current_networks = set()
    def __init__(self):
        self.host = '10.60.0.114'
        self.user = 'icmrsu'
        self.secret = 'gr@peb1ke'
        self.port = 22
        self.conf_file_path = '/etc/quagga/bgpd.conf'
        #logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level=logging.INFO)
        # Зададим параметры логгирования
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        file_handler = logging.FileHandler('dns-sniffer.log')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def read_current_networks(self):
        """
        Получаем уже заданные IP адреса  сетей из файла конфигурации Quagga
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.host, username=self.user, password=self.secret, port=self.port)
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
        host = '10.60.0.114'
        port = '2605'
        user = r'mrsu'
        password = r'gr@peb1ke'
        telnet = telnetlib.Telnet(host, port, 3)
        telnet.read_until('Password: ', 3)
        telnet.write(password + '\r\n')
        telnet.expect([re.compile('.*>\s'), ], 3)
        telnet.write('en' + '\r\n')
        telnet.read_until('Password: ', 3)
        telnet.write(password + '\r\n')
        telnet.expect([re.compile('.*#\s'), ], 3)
        telnet.write('term len 0' + '\r\n')
        telnet.expect([re.compile('.*#\s'), ], 3)
        return telnet

q = QuaggaConfig()
q.read_current_networks()