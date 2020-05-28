source /etc/profile
cd /opt/production/stocktick/bin
dte=$(date +"%Y%m%d")
mkdir -p "../log/${dte}"
echo $(pwd)

nohup /usr/bin/python HHTick.py 1>"../log/${dte}/HHTick_stdout.log" 2>"../log/${dte}/HHTick_stderr.log" &
