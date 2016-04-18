# -*- coding: utf-8 -*-

import pcap
import pika

print 'ok'
pc = pcap.pcap()
pc.setfilter('udp src port 53')

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='dns')


for ts, pkt in pc:
    channel.basic_publish(exchange='', routing_key='dns', body=pkt)
connection.close()


