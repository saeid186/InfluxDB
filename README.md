# InfluxDB
please add the perfdata.conf file to the /etc/perfdata/ directory

if you need rotate the log file add the logrotate to the /etc/logrotate.d/perfdata 

to create perfdata as a service please create the /etc/systemd/system/perfdata.service and add the file perfdata.service to it.
then run 
systemctl daemon-reload
systemctl enable perfdata
systemctl start perfdata

