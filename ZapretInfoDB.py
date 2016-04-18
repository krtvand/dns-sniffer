# -*- coding: utf-8 -*-

import logging
import redis
import paramiko
from ZapretInfoXMLParser import ZapretInfoXMLParser
from QuaggaConfig import QuaggaConfig


class ZapretInfoDB(object):

    def __init__(self):
        self.host = '194.54.64.53'
        self.user = 'icmrsu'
        self.secret = 'gr@peb1ke'
        self.port = 22
        self.dump_file_path = '/gost-ssl/rzs/dump/dump.xml'
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.quagga = QuaggaConfig()

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
        self.r.sadd('domains', 'test.ru')
        self.r.sadd('test.ru', '0.1.1.1')
        self.r.sadd('domains', 'test.ru2')
        self.r.sadd('test.ru2', '0.1.1.2')

    def update_domains(self):
        # Получаем обновленный дамп реестра запрещенных сайтов с удаленного сервера по SFTP
        # и загружаем его в базу данных Redis
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.host, username=self.user, password=self.secret, port=self.port)
        sftp = client.open_sftp()

        self.logger.info('Start updating Redis ZapretInfo database from new xml dump...')
        with sftp.open(self.dump_file_path, 'r') as f:
            zapret_info_xml = ZapretInfoXMLParser(f)
            zapret_info_xml.get_domains()
            for domain in zapret_info_xml.domains:
                self.r.sadd('new_domains', domain)
            self.logger.info('New ZapretInfo dump contain %s domains' % len(zapret_info_xml.domains))

        # Получаем список доменов, которые были исключены из Реестра запрещенных сайтов
        self.r.sdiffstore('domains_for_delete', 'domains', 'new_domains')
        self.logger.info('After update required for delete %s domains' % self.r.scard('domains_for_delete'))
        # Подмениваем текущий список доменов обновленным
        self.r.rename('new_domains', 'domains')
        # Удаляем устаревшие домены и их IP адреса из базы данных Redis и BGP конфигурации Quagga
        self.delete_domains()

    def delete_domains(self):
        # Удаляем устаревшие домены и их IP адреса из базы данных Redis и BGP конфигурации Quagga
        ip_for_delete = set()
        # Удаляем все множества с IP адресами для доменов, которые были исключены из Реестра запрещенных сайтов
        #for d in range(self.r.scard('domains_for_delete')):
        #    domain = self.r.spop('domains_for_delete')
        for domain in self.r.smembers('domains_for_delete'):
            # Сначала определим и сохраним множество IP адресов всех доменов которые необходимо удалить из Quagga
            ip_for_delete = ip_for_delete.union(self.r.smembers(domain))
            # Затем удаляем само множесвво из базы данных Redis
            self.logger.info('deleted domain ' + domain.encode('utf-8') + ' from Redis database')
            self.logger.info('domain %s had following addresses: %s' % (domain.encode('utf-8'), self.r.smembers(domain)))
            self.r.delete(domain)
        # Удаляем из Quagga определенные ранее IP адреса, домены которых были исключены из реестра запрещенных сайтов
        if ip_for_delete:
            self.quagga.delete_bgp_networks(ip_for_delete)

    def add_domains(self):
        # Добавляем в конфигурацию Quagga накопившиеся в базе Redis новые IP адреса
        # для доменов из реестра запрещенных сайтов
        current_ip_set = set()
        for domain in self.r.smembers('domains'):
            current_ip_set = current_ip_set.union(self.r.smembers(domain))
        self.logger.info('Current Redis database contain %s IP addresses' % len(current_ip_set))

        # Из множества IP адресов которые занесены в базу данных Redis вычитаем
        # множество IP адресов из конфигурации Quagga.
        # В итоге получаем набор адресов, которе необходимо занести в Quagga
        ip_for_add = current_ip_set.difference(self.quagga.read_current_networks())
        if ip_for_add:
            self.quagga.add_bgp_networks(ip_for_add)
        else:
            self.logger.info('Nothing to add in quagga')

if __name__ == "__main__":
    z = ZapretInfoDB()
    z.update_domains()
    z.add_domains()