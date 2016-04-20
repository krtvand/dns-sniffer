# -*- coding: utf-8 -*-
#!/usr/bin/python

import sys
import getopt

import pcap
import pika

def main(argv):
    """
    Запускается сниффер и полученыые пакеты передаются в очередь RubbitMQ
    :param argv: В качестве аргументов принимает название интерфейса,
    который необходимо прослушивать
    """
    try:
        opts, args = getopt.getopt(argv, "hi:", ["interface="])
    except getopt.GetoptError:
        print 'dns-sniffer.py -i <interface>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'dns-sniffer.py -i <interface>'
            sys.exit()
        elif opt in ("-i", "--interface"):
            interface = arg
    pc = pcap.pcap(name=interface)
    pc.setfilter('udp src port 53')

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='dns')


    for ts, pkt in pc:
        channel.basic_publish(exchange='', routing_key='dns', body=pkt)
    connection.close()

if __name__ == "__main__":
   main(sys.argv[1:])

