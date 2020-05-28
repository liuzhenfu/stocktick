source /etc/profile
cd /opt/production/stocktick/bin
dte=$(date +"%Y%m%d")
if [ $# == "1" ];then
    dte=$1
fi
mkdir -p "../log/${dte}"
echo $(pwd)


echo "start download SH L2 market data"
/usr/bin/python hdfgetL2.py $dte 1>"../log/${dte}/hdfgetL2_stdout.log" 2>"../log/${dte}/hdfgetL2_stderr.log"
echo "down done"