# -*- coding: utf-8 -*-
#!/usr/bin/python

#DUMP_FILE_PATH = '/home/andrew/dump.xml'

import xml.etree.ElementTree as etree
from urlparse import urlparse
import re

# TODO
# в одной реестрововй записи может содержаться несколько элементов URL,
# т.е. вместо метода elem_content.find('url'), необходимо использовать findall

class ZapretInfoXMLParser(object):


    def __init__(self, dump_file_or_path):
        self.tree = etree.parse(dump_file_or_path)
        self.root = self.tree.getroot()
        self.domains = set()
        self.domains_from_url = set()

    def get_unicode_text_from_xml_element(self, element):
        # Модуль xml.etree.ElementTree парсит XML файл и сохраняет значения
        # элементов в байтовой строке, но в случае с кириллицей,
        # модуль хранит текст в юникоде. В нашей системе все строки
        # мы храним в юникоде, поэтому все строки приводи к юникоду
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



if __name__ == "__main__":
    zi = ZapretInfoXMLParser('/home/andrew/dump.xml')
    print len(zi.get_data_for_checker())

#print len(zi.domains)
#print len(zi.domains_from_url)