# -*- coding: utf-8 -*-

#DUMP_FILE_PATH = '/home/andrew/dump.xml'

import xml.etree.ElementTree as etree
from urlparse import urlparse
import urllib
import re


class ZapretInfoXMLParser(object):

    def __init__(self, dump_file_or_path):
        self.tree = etree.parse(dump_file_or_path)
        self.root = self.tree.getroot()
        self.domains = set()
        self.domains_from_url = set()

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
                # Но некоторые записи парсер уже хранит в юникоде, чаще всего это кириллические домены.
                # Поэтому преобразовываем их в формат idna
                except:
                    self.domains.add(domain.text.encode('idna'))
                 #   print "non latin domain: ", domain.text, ' idna: ', domain.text.encode('idna')
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


#zi = ZapretInfoXMLParser('/home/andrew/dump.xml')
#zi.get_domains()

#print len(zi.domains)
#print len(zi.domains_from_url)