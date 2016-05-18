# -*- coding: utf-8 -*-
#!/usr/bin/python

#DUMP_FILE_PATH = '/home/andrew/dump.xml'

import logging
import urllib
import re
import sys

import paramiko
import xml.etree.ElementTree as etree
from urlparse import urlparse

# TODO
# в одной реестрововй записи может содержаться несколько элементов URL,
# т.е. вместо метода elem_content.find('url'), необходимо использовать findall

class ZapretInfoXMLParser(object):


    def __init__(self, dump_file_or_path):
        self.tree = etree.parse(dump_file_or_path)
        self.root = self.tree.getroot()
        self.domains = set()
        self.domains_from_url = set()
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

    def get_unicode_text_from_xml_element(self, element):
        # Модуль xml.etree.ElementTree парсит XML файл и сохраняет значения
        # элементов в байтовой строке, но в случае с кириллицей,
        # модуль хранит текст в юникоде. В нашей системе все строки
        # мы храним в юникоде, поэтому все строки приводим к юникоду
        #
        if isinstance(element.text, unicode):
            return element.text
        else:
            return element.text.decode('cp1251')

    def get_domains(self):
        """
        Получаем список доменов из XML файла из элемента "domain".
        """
        for elem in self.root:
            sub_elem_domain = elem.iter('domain')
            for domain in sub_elem_domain:
                # Получаем домен и декодируем его из str в юникод
                try:
                    self.domains.add(domain.text.decode('cp1251'))
                # Но некоторые записи парсер уже хранит в юникоде,
                # чаще всего это кириллические домены.
                # Поэтому преобразовываем их в формат idna
                except:
                    self.domains.add(domain.text.encode('idna'))
        return self.domains

    def get_domains_from_url(self):
        """
        Получаем список доменов из XML файла из элемента url.
        Опытным путем проверено, что множество доменов полученных из "url" адресов
        является подмножеством доменов, полученыых из элемента "domain".
                :return: возвращает множество доменов
        """
        for elem in self.root:
            sub_elem_url = elem.iter('url')
            for url_elem in sub_elem_url:
                try:
                    url = url_elem.text.decode('cp1251')
                except:
                    url = url_elem.text
                # Выделяем имя домены из url адреса
                url = urlparse(url).netloc
                # Приводим к нижнему регистру
                url = url.lower()
                # убираем номер порта из текущей записи (domain.com:5050 => domain.com)
                url = re.sub(r':[0-9]*$', '', url)
                # Преобразовываем домен в формат idna
                url = url.encode('idna')
                # Добавляем к списку доменов
                self.domains_from_url.add(url)
        return self.domains_from_url

    def get_data_for_checker(self):
        """
        Функция возвращает URL адреса и адреса доменов для проверки их на доступность.
        Данные из XML дамп файла выбираем по следующему алгоритму:
        - Если в реестровой записи есть URL, выбираем его
        - Если нет URL записи, но есть доменное имя, добавляем к общему списку домен
        - IP адреса в текущей версии не проверяются
        """
        data_for_check = set()
        for elem_content in self.root:
            elem_url = elem_content.find('url')
            if elem_url is not None:
                url = self.get_unicode_text_from_xml_element(elem_url)
                data_for_check.add(url)
            else:
                elem_domain = elem_content.find('domain')
                if elem_domain is not None:
                    domain = self.get_unicode_text_from_xml_element(elem_domain)
                    scheme = urlparse(domain).scheme
                    if not scheme:
                        domain = u'http://' + domain
                    data_for_check.add(domain)
        return data_for_check

    def load_data_to_squidguard(self):
        # Множество url адресов
        urls = set()
        # Множество url адресов, содержащих кириллицу и прочие не ISCII символы
        urls_non_ascii = set()
        # Множество доменов для блокировки
        domains = set()
        # Множество доменов из https url адресов
        domains_from_https = set()
        for elem_content in self.root:
            # Вначале перебираем url записи
            url_elems = elem_content.findall('url')
            for url_elem in url_elems:
                # Получаем юникод строку
                url = self.get_unicode_text_from_xml_element(url_elem)
                # Если это https сайт, то его домен необходимо занести
                # в отдельное множество, т.к. этого требует логика SquidGuard
                if re.search(ur'^https://', url) is not None:
                    # убираем поддомен "www" для улучшения качества фильтрации,
                    # т.к. если обратиться по адресу www1.domain.ru,
                    # то SquidGuard пропустит такой запрос
                    domain_from_https = re.sub(ur'^www\d*\.', '', urlparse(url).netloc)
                    domains_from_https.add(domain_from_https)
                url = re.sub(ur'^https?://', '', url)
                url = re.sub(ur'//$', '/', url)
                url = re.sub(ur'^([^/]+)\.(/+.*)$', ur'\1\2', url)
                url = re.sub(ur'^([^/]+)\.$', ur'\1', url)
                url = re.sub(ur'^(.*/+)\.$', ur'\1', url)
                urls.add(url)
                # Кириллические записи мы храним в базе SquidGuard
                # как в utf-8 формате, так и в cp1251.
                # Т.к. SquidGuard чувствителен к кодировке
                if re.search(ur'[А-яёЁ]+', url) is not None:
                    url = url.replace(ur' ', ur'%20')
                    urls_non_ascii.add(url)
            # Переходим к обработке доменов только
            # в том случае, если отсутствует url запись
            if url_elems is not None:
                continue
            domain_elems = elem_content.findall('domain')
            if domain_elems is not None:
                for domain in domain_elems:
                    domain = self.get_unicode_text_from_xml_element(domain)
                    domain = urlparse(domain).netloc
                    domain = re.sub(ur'^www\d*\.', '', domain)
                    domains.add(domain)
                    print domain
            ip_elems = elem_content.findall('ip')

        print len(urls), 'Указателей всего'
        print len(urls_non_ascii), 'Указателей содержащик кириллицу'
        print len(domains), 'Доменов всего'
        print len(domains_from_https), 'Доменов всего + домены https ссылок'

        with open('/home/andrew/pornurls', 'wb') as f:
            for url in urls:
                url = urllib.unquote(url.encode('utf-8'))
                url = url.replace(r' ', r'%20')
                f.write("%s\n" % url)
        with open('/home/andrew/cp1251urls', 'wb') as f:
            for url in urls_non_ascii:
                f.write("%s\n" % url)
        with open('/home/andrew/domains', 'wb') as f:
            for domain in domains:
                domain = domain.replace(ur' ', r'%20')
                f.write("%s\n" % domain)
        with open('/home/andrew/blocked_https.txt', 'wb') as f:
            for domain in domains_from_https:
                domain = domain.replace(ur' ', r'%20')
                f.write("%s\n" % domain)

if __name__ == "__main__":
    DUMP_HOST = '194.54.64.53'
    DUMP_HOST_SSH_LOGIN = 'icmrsu'
    DUMP_HOST_SSH_SECRET = 'bl@ckbr@1n'
    DUMP_HOST_SSH_PORT = 22
    DUMP_FILE_PATH = '/gost-ssl/rzs/dump/dump.xml'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=DUMP_HOST, username=DUMP_HOST_SSH_LOGIN,
                   password=DUMP_HOST_SSH_SECRET, port=DUMP_HOST_SSH_PORT)
    sftp = client.open_sftp()
    print 'Load dump...'
    with sftp.open(DUMP_FILE_PATH, 'r') as f:
        zi = ZapretInfoXMLParser(f)
        zi.load_data_to_squidguard()
    print 'ok'

#print len(zi.domains)
#print len(zi.domains_from_url)