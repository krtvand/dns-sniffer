# -*- coding: utf-8 -*-
#!/usr/bin/python

import logging
import sys

import paramiko
import requests
from requests.exceptions import RequestException

from ZapretInfoXMLParser import ZapretInfoXMLParser

class ZapretInfoChecker(object):


    """ Класс предназначен для проверки качества фильтрации
    трафика по реестру роскомнадзора

    """
    def __init__(self):
        self.host = '194.54.64.53'
        self.user = 'icmrsu'
        self.secret = 'gr@peb1ke'
        self.port = 22
        self.dump_file_path = '/gost-ssl/rzs/dump/dump.xml'
        # Зададим параметры логгирования
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(u'%(levelname)-8s [%(asctime)s]  %(message)s')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        file_handler = logging.FileHandler('zapret-info-checker.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def get_data_for_check(self):
        """ Получаем информацию для осуществления проверки на доступность
        :return: Множество URL и доменов для проверки
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.host, username=self.user, password=self.secret, port=self.port)
        sftp = client.open_sftp()
        self.logger.info('Opening XML dump...')
        with sftp.open(self.dump_file_path, 'r') as f:
            zapret_info_xml = ZapretInfoXMLParser(f)
            data_for_chek = zapret_info_xml.get_data_for_checker()
        return data_for_chek

    def check_availability(self):
        data_for_check = self.get_data_for_check()
        data_for_check_len = len(data_for_check)
        self.logger.info('Loaded %s sites for check availability' % data_for_check_len)
        count = 1
        for elem in data_for_check:
            results = {}
            try:
                r = requests.get(elem, timeout=10, verify=False)
                results[elem] = r.status_code
                self.logger.debug('Checking (%s/%s) %s, response code: %s' % (count, data_for_check_len, elem, r.status_code))
                count += 1
            except RequestException as e:
                results[elem] = e
                count += 1
                self.logger.warning('Checking (%s/%s) %s, error: %s' % (count, data_for_check_len, elem, e))
        available_sites = set()
        for key in results:
            if results[key] == 200:
                available_sites.add(key)
        self.logger.info('Overall available sites: %s' % len(available_sites))

z = ZapretInfoChecker()
z.check_availability()





