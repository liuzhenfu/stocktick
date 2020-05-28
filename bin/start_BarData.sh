source /etc/profile
cd /opt/production/stocktick/bin
dte=$(date +"%Y%m%d")
mkdir -p "../log/${dte}"
echo $(pwd)

nohup /usr/bin/python getBarData.py 1>"../log/${dte}/getBarData_stdout.log" 2>"../log/${dte}/getBarData_stderr.log" &