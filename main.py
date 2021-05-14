import logging
import threading
import time
import concurrent.futures
import os
import shutil
import re
from timeit import default_timer as timer

class create_thread:
    def __init__(self):
        self.value = 0


    def init_influxdb_client(self):
        global db

        if 3 == 3:
            try:
                from influxdb import InfluxDBClient
            except ImportError as e:
                log.exception("Could not import influxdb module: {0}".format(e))
                sys.exit(1) 
            db = InfluxDBClient(
                host= 'localhost',#cfg['influxdb']['host'],
                port='8086',#cfg['influxdb']['port'],
                username='nagios',#cfg['influxdb']['username'],
                password='nagios@123',#cfg['influxdb']['password'],
                database='test'#cfg['influxdb']['database'],
                #ssl=cfg['influxdb']['ssl'],
                #verify_ssl=cfg['influxdb']['verify_ssl'],
                #timeout=float(cfg['influxdb']['timeout']),
                #use_udp=cfg['influxdb']['use_udp'],
                #udp_port=cfg['influxdb']['udp_port'],
                #proxies=cfg['influxdb']['proxies']
            )
        else:
            try:
                from influxdb import InfluxDBClusterClient
            except ImportError as e:
                log.exception("Could not import influxdb module: {0}".format(e))
            db = InfluxDBClusterClient(
                hosts=cfg['influxdb']['hosts'],
                username=cfg['influxdb']['username'],
                password=cfg['influxdb']['password'],
                database=cfg['influxdb']['database'],
                ssl=cfg['influxdb']['ssl'],
                verify_ssl=cfg['influxdb']['verify_ssl'],
                timeout=float(cfg['influxdb']['timeout']),
                use_udp=cfg['influxdb']['use_udp'],
                udp_port=cfg['influxdb']['udp_port'],
                shuffle=cfg['influxdb']['shuffle'],
                healing_delay=cfg['influxdb']['healing_delay']
            ) 

    def send_points(self,points):
        """
        param points: list of points to send to influxdb
        return: True on success, False otherwise
        """
        try:
            db.write_points(
                points
            #    time_precision='s', 
            #    tags=cfg['fluxios']['extra_tags'],
            #    batch_size=int(cfg['fluxios']['batch_size'])
            )
        except Exception as e:
            logging.error(("Exception while trying to write points: {0}")
                .format(e))
            return False

        return True

    def check_skip_file(self , file_name):
        """
        param file: Full path to file to check
        return: True if the file should be skipped, False otherwise
        """
        if (
            file_name == "host-perfdata" or
            file_name == "service-perfdata"
        ):
            return True
        elif re.match('^_', file_name):
            return True

        if os.stat(file_name)[6] == 0:
            logging.info(f"Found empty file, moving file: {file_name} without processing.")
            shutil.move(f'{file_name}','/tmp/influx/processed/')
            #rm_file(file_name)
            return True

        if os.path.isdir(file_name):
            return True

        if 'thread' in file_name:
            return True

        return False
  

    def process_perfdata_file(self , file_name):
        processed_lines = 0
        skipped_lines = 0
        points = []
        perfdata_re = "^'?([^=']+)'?=(U|[\d\.\-]+)([\w\/%]*);?([\d\.\-:~@]+)?;?([\d\.\-:~@]+)?;?([\d\.\-]+)?;?([\d\.\-]+)?;?\s*"
        try:
            file = open(file_name, "r")
            file_array = file.readlines()
            file.close()
        except (IOError, OSError) as ex:
            logging.info(f"Can't open file: {file_name} error: {ex}")
            return False
        # parse each line
        for line in file_array:
            processed_lines += 1
            try:
                line_dict = dict(re.split('::', x, 1) for x in line.split('\t'))
            except Exception as e:
                skipped_lines += 1
                logging.info(f"{e}: Could not parse perfdata line into key::value pairs in file {file_name}, skipping: {line}")
                if skipped_lines == len(file_array):
                    logging.info(f"file : {file_name} skipped because all line skipped")
                    os.rename(file_name,f'{file_name}-skipped')
                continue
            # pick out values from the line
            if line_dict['DATATYPE'] == "SERVICEPERFDATA":
                service_description = line_dict['SERVICEDESC']
                perfdata = line_dict['SERVICEPERFDATA']
                if not perfdata:
                    skipped_lines += 1
                    logging.info(f"perfdata string is empty while reading line file {file_name}: {line}")
                    continue
                check_command = line_dict['SERVICECHECKCOMMAND'].split('!')[0]
            elif line_dict['DATATYPE'] == "HOSTPERFDATA":
                service_description = "__host__"
                perfdata = line_dict['HOSTPERFDATA']
                check_command = line_dict['HOSTCHECKCOMMAND'].split('!')[0]
            else:
                skipped_lines += 1
                logging.info(f"Unknown DATATYPE, skipping: '{line_dict['DATATYPE']}'")
                continue
            host_name = line_dict['HOSTNAME']
            timestamp = line_dict['TIMET']
            # extract individual metrics from the perfdata string
            for metric in re.findall("(.*?=.+?)\s", perfdata + ' '):
                m = re.search(perfdata_re, metric)
                if m:
                    (label, value, uom, warn, crit, min, max) = m.groups()
                    numeric_fields = {
                        "value": value,
                        "warn": warn,
                        "crit": crit,
                        "min": min,
                        "max": max
                    }
                    fields = {"label": label, "uom": uom}
                    for field, value in numeric_fields.items():
                        if value is not None and value.strip():
                            value = re.sub('[^0-9.]','', value)
                            try:
                                fields[field] = float(value)
                            except ValueError:
                                logging.info(f"Failed to float() '{field}' = '{value}' for '{service_description}'@'{host_name}'")
                    tags = {
                        "service_description": service_description,
                        "host_name": host_name,
                        "metric": label
                    }
            
                    point = {
                        "measurement": check_command,
                        "timestamp": timestamp,
                        "fields": fields,
                        "tags": tags
                    }
                    points.append(point)
                else:
                    logging.info(f"perfdata metric from file {file} did not match, skipping: {metric}")
            # END: for
        #logging.info(f"Processed {processed_lines}/{processed_lines+skipped_lines} lines into {len(points)} points in {round(end-start, 2)} seconds ({round(processed_lines/(end-start))} lines/sec, {round(len(points)/(end-start))} pts/sec")
        return points
        
    def update(self, name,file_name):
        try:
            start = timer()
            #self.influxdb(name ,  file_name)
            os.rename(file_name,f'{file_name}-processing')
            points = self.process_perfdata_file(f"{file_name}-processing")
            logging.info(f"before send point ")
            self.send_points(points)
            logging.info(f"after send point")
            #self.influxdb(name ,  file_name)
            end = timer()
        except tweepy.error.TweepError as e:
            logging.info("Thread %s: error with %e", name, e)
            pass


def loop_file():
    global total_file , max_workers , max_index
    max_workers= 4
    max_index = 0
    files = os.listdir('/tmp/influx/')
    total_file = []
    for file in files:
        if 'txt' in file and 'processing' not in file and 'skipped' not in file :
            if create_thread.check_skip_file(file):
                continue
            else:
                total_file.append(file)
    total_file = sorted(total_file)
    if len(total_file) > max_workers:
        max_index = max_workers
    else:
        max_index = len(total_file)
    



if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    create_thread = create_thread()
    create_thread.init_influxdb_client()
    while True:
        loop_file()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        for index in range(max_index):
            if max_workers < threading.active_count()-1 :
                continue
            else:
                logging.info(f"trying for file  {total_file[index]} and total len is {max_index}")
                executor.submit(create_thread.update, total_file[index],total_file[index])
        logging.info(f"total live thrad is {threading.active_count()-1}")
        time.sleep(2)
