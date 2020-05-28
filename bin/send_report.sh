# this script will be executed on 192.168.1.16
dte=$(date +"%Y%m%d")
echo $dte

report_path="192.168.1.216:/home/operation/production/stocktick/report/${dte}"
scp -r $report_path ~/mailpool/

if [[ $? == 0 ]]
then
    cd ~/mailpool
    /usr/local/bin/python send_report.py
    rm -rf $dte
fi
