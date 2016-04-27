# -*- coding: utf-8 -*-
#!/usr/bin/python

import logging
import sys
from multiprocessing import Pool, cpu_count
import time
import pycurl
try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

import paramiko
import requests
from requests.exceptions import RequestException

from ZapretInfoXMLParser import ZapretInfoXMLParser

# init
host = '194.54.64.53'
user = 'icmrsu'
secret = 'gr@peb1ke'
port = 22
dump_file_path = '/gost-ssl/rzs/dump/dump.xml'
# Зададим параметры логгирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(u'%(levelname)-8s [%(asctime)s]  %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
file_handler = logging.FileHandler('zapret-info-checker.log', mode='w')
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def get_data_for_check():
    """ Получаем информацию для осуществления проверки на доступность
        :return: Множество URL и доменов для проверки
        """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=user, password=secret, port=port)
    sftp = client.open_sftp()
    logger.info('Opening XML dump...')
    with sftp.open(dump_file_path, 'r') as f:
        zapret_info_xml = ZapretInfoXMLParser(f)
        result = zapret_info_xml.get_data_for_checker()
    return result
# Функция проверки одного сайта
def make_request(site):
    buffer_ = BytesIO()
    result = {}
    c = pycurl.Curl()
    c.setopt(c.URL, site)
    c.setopt(c.WRITEDATA, buffer_)
    c.setopt(c.FOLLOWLOCATION, True)
    try:
        c.perform()
        result[site] = str(c.getinfo(c.RESPONSE_CODE))
        if c.getinfo(c.RESPONSE_CODE) == 200:
            logger.warning(site)
        logger.debug('Checking %s, response code: %s' % (site, c.getinfo(c.RESPONSE_CODE)))

    except Exception as e:
        result[site] = str(e)
        logger.debug('Checking %s, error: %s' % (site, e))
    return result

# Сам процесс проверки
data_for_check = get_data_for_check()
logger.info('Start checking...')
pool = Pool(100)
start_time = time.time()
results = pool.map(make_request, data_for_check)
pool.close()
pool.join()
logger.info("Elapsed time: {:.3f} sec".format(time.time() - start_time))

available_sites = set()
for it in results:
    if it.values()[0] == 200:
        available_sites.add(it.keys()[0])
logger.info('Overall available sites: %s' % len(available_sites))