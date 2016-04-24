# -*- coding: utf-8 -*-
#!/usr/bin/python

import logging
import sys
from multiprocessing import Pool, cpu_count
import time

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
file_handler = logging.FileHandler('zapret-info-checker.log')
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

def make_request(site):
    result = {}
    try:
        r = requests.get(site, timeout=5, verify=False)
        result[site] = r.status_code
        logger.debug('Checking %s, response code: %s' % (site, r.status_code))
    except RequestException as e:
        result[site] = e
        logger.debug('Checking %s, error: %s' % (site, e))
    return result

data_for_check = get_data_for_check()
test_data_for_check = set()
for i in range(1000):
    test_data_for_check.add(data_for_check.pop())


logger.info('Loaded %s sites for check availability' % len(data_for_check))
pool = Pool(80)
start_time = time.time()
results = pool.map(make_request, test_data_for_check)
pool.close()
pool.join()
logger.info("Elapsed time: {:.3f} sec".format(time.time() - start_time))
logger.info('results lenght: %s' % (len(results)))

pool = Pool(100)
start_time = time.time()
results = pool.map(make_request, test_data_for_check)
pool.close()
pool.join()
logger.info("Elapsed time: {:.3f} sec".format(time.time() - start_time))
logger.info('results lenght: %s' % (len(results)))

pool = Pool(150)
start_time = time.time()
results = pool.map(make_request, test_data_for_check)
pool.close()
pool.join()
logger.info("Elapsed time: {:.3f} sec".format(time.time() - start_time))
logger.info('results lenght: %s' % (len(results)))

pool = Pool(300)
start_time = time.time()
results = pool.map(make_request, test_data_for_check)
pool.close()
pool.join()
logger.info("Elapsed time: {:.3f} sec".format(time.time() - start_time))
logger.info('results lenght: %s' % (len(results)))

pool = Pool(400)
start_time = time.time()
results = pool.map(make_request, test_data_for_check)
pool.close()
pool.join()
logger.info("Elapsed time: {:.3f} sec".format(time.time() - start_time))
logger.info('results lenght: %s' % (len(results)))