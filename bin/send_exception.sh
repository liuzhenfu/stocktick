# this script will be executed on 192.168.1.16
dte=$(date +"%Y%m%d")
echo $dte

report_path="192.168.1.216:/home/operation/production/stocktick/log/${dte}/error.message"
scp $report_path ~/mailpool/

if [[ $? == 0 ]]
then
    cd ~/mailpool
    /usr/local/bin/python send_exception.py
fi
