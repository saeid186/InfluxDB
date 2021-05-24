#!/bin/bash

######### zip folder processed ###########
date=$(date +"%Y%m%d")
source_path="/var/log/influxdb/perfdata/processed/"
des_path='/var/log/influxdb/perfdata/'
file_name="processed-$date.zip"

zip -qrm $des_path$file_name $source_path

######### remove old zip file ###########
counter=0
stored_zip_file=15
total_file=$(ls -lrth /var/log/influxdb/perfdata/*.zip |awk '{print $9}')
for i in $test_files
do
((counter=$counter+1))
if [[ $counter -gt $stored_zip_file ]]
then
file_remove=$(ls -lrth /var/log/influxdb/perfdata/*.zip |awk '{print $9}' |head -n2 |tail -n 1)
rm -rf  /var/log/influxdb/perfdata/$file_remove
fi
done

