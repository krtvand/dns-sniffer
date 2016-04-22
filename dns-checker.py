# -*- coding: utf-8 -*-
#!/usr/bin/python

LOCAL_DNS_SERVERS = {'10.73.73.73', '10.73.10.73'}

import logging
import socket

import pika
import dpkt
import redis


# Зададим параметры логгирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
file_handler = logging.FileHandler('dns-sniffer.log')
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_declare(queue='dns')

# Подключаемся к базе данных Redis, где хранится информация о списке запрещенных доменов
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# начинаем искать полученные пакеты в списке запрещенных доменов
print ' [*] Waiting for messages. To exit press CTRL+C'

def callback(ch, method, properties, body):
    try:
        eth = dpkt.ethernet.Ethernet(body)
        ip = eth.data
        udp = ip.data
        dns = dpkt.dns.DNS(udp.data)
    except Exception as e:
        logger.warning(e.message)
        pass
    if dns.qr == 1 and len(dns.an) > 0:
        name = dns.an[0].name
        # idna - формат представления кириллических доменов в специальном виде типа xn--...
        #print name, name.decode('idna')
        logger.debug('Found dns response for %s (idna: %s)' % (name.decode('idna'), name))
        if r.sismember('domains', name):
            for rr in dns.an:
                if rr.type == dpkt.dns.DNS_A:
                    ip_addr = socket.inet_ntoa(rr.ip)
                    # В сети университета действует система блокировки доступа
                    # к ресурсам по DNS, поэтому могут возникать DNS ответы
                    # с адресами локальных DNS-серверов
                    if ip_addr not in LOCAL_DNS_SERVERS:
                        r.sadd(name, socket.inet_ntoa(rr.ip))
                        logger.info('Found IP address %s for domain from ZapretInfo: %s' % (socket.inet_ntoa(rr.ip), rr.name))

channel.basic_consume(callback, queue='dns', no_ack=True)
channel.start_consuming()
