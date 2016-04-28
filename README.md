# dns-sniffer
DNS sniffer предназначен для прослушивания сетевого трафика с целью выявления IP адресов ресурсов из реестра запрещенных сайтов

Для работы скриптов необходимо наличие следующих установленных приложений и модулей Python:
  Redis http://redis.io/
  RabbitMQ http://www.rabbitmq.com/

  Python модули:
    redis - https://pypi.python.org/pypi/redi
    pypcap - https://pypi.python.org/pypi/pypcap
    pika - https://pypi.python.org/pypi/pika
    dpkt - https://pypi.python.org/pypi/dpkt
    paramiko - https://pypi.python.org/pypi/paramiko/
  Для работы скрипта проверки доступности сайтов необходимы дополнительные модули, которые обеспечивают вставку SNI информаци в HTTPS запрос. Подробности тут: http://stackoverflow.com/questions/18578439/using-requests-with-tls-doesnt-give-sni-support:
    pyOpenSSL
    ndg-httpsclient
    pyasn1
