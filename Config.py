# file_path = "/tmp/influx/"
# max_worker = 500
# sleep_time = 2
# destination_path = "/var/log/influxdb/perfdata/processed"
# log_file = "/var/log/influxdb/perfdata/perfdata.log"
# host = "10.104.55.66"
# hosts = "'10.104.55.66' , '10.104.55.66'"
# port = 8086
# username = "nagios"
# password = "nagios@123"
# database = "nagios"
# cluster = False

[perfdata]

spool_directory = "/var/spool/nagios/fluxios/"
file_path = "/tmp/influx/"
log_file = "/var/log/influxdb/perfdata/perfdata.log"
destination_path = "/var/log/influxdb/perfdata/processed/"
max_worker = 500
sleep_time = 2
log_max_size = 24
log_keep = 4
log_level = logging.INFO
interval = 15
batch_size = 500






[influxdb]

host = "127.0.0.1"
port = 8086
proxies = None
cluster = False
shuffle = True
healing_delay = 900
ssl = False
verify_ssl = True
timeout = 15
database = nagios
username = nagios
password = nagios@123
use_udp = False
udp_port = 4444
