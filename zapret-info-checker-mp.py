# -*- coding: utf-8 -*-
#!/usr/bin/python

"""
Скрипт предназначен для проверки качества фильтрации трафика
по реестру роскомнадзора в многопроцессном режиме
Для корректной проверки https требуется SNI информация от клиента
"""
DUMP_HOST = '194.54.64.53'
DUMP_HOST_SSH_LOGIN = 'icmrsu'
DUMP_HOST_SSH_SECRET = 'bl@ckbr@1n'
DUMP_HOST_SSH_PORT = 22
DUMP_FILE_PATH = '/gost-ssl/rzs/dump/dump.xml'

import logging
import sys
from multiprocessing import Pool, cpu_count
import time

import paramiko
import requests
from requests.exceptions import RequestException

from ZapretInfoXMLParser import ZapretInfoXMLParser

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
    client.connect(hostname=DUMP_HOST, username=DUMP_HOST_SSH_LOGIN, password=DUMP_HOST_SSH_SECRET, port=DUMP_HOST_SSH_PORT)
    sftp = client.open_sftp()
    logger.info('Opening XML dump...')
    with sftp.open(DUMP_FILE_PATH, 'r') as f:
        zapret_info_xml = ZapretInfoXMLParser(f)
        result = zapret_info_xml.get_data_for_checker()
    return result

def make_request(site):
    """Функция проверки доступности одного сайта
    :param site: Адрес сайта для проверки
    :return: Dictionary, где ключ - сайт, значение - код ответа (200, 404)
    """
    result = {}
    try:
        r = requests.get(site, timeout=10, verify=True)
        result[site] = r.status_code
        # Если код ответа веб сервера 200, значит сайт доступен
        if r.status_code == 200:
            logger.warning('Site is availble: %s responce code: %s' %
                           (site, r.status_code))
        logger.debug('Checking %s, response code: %s' % (site, r.status_code))
    # Обрабатываем ошибки модуля Requests
    except RequestException as e:
        result[site] = -1
        logger.debug('Error %s, message: %s' % (site, e))
    # Пропускаем прочие ошибки подключения
    except:
        result[site] = -1
        logger.debug('Error: %s Other exception' % site)
    return result

# Получаем данные для проверки из свежего DUMP файла
data_for_check = get_data_for_check()
# Сам процесс проверки
logger.info('Start checking...')
# Определяем количество одновременно работающих процессов
# как произведение количества ядер и числа 100.
# Большее количество чем 100 замедляем процесс проверки.
# Проверено эмпирическим путем.
pool_count = cpu_count() * 100
pool = Pool(pool_count)
start_time = time.time()
results = pool.map(make_request, data_for_check)
pool.close()
pool.join()
logger.info("Elapsed time: {:.2f} sec".format(time.time() - start_time))
# Подсчитываем количество доступных сайтов
available_sites = set()
for it in results:
    # Если код ответа веб сервера 200, значит сайт доступен
    if it.values()[0] == 200:
        available_sites.add(it.keys()[0])
logger.info('Overall available sites: %s (%2.2f percentage) of %s' %
            (len(available_sites), 100.0*len(available_sites)/len(data_for_check),
             len(data_for_check)))