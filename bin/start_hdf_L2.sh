source /etc/profile
cd /datas/production/stocktick/bin
dte=$(date +"%Y%m%d")
if [ $# == "1" ];then
    dte=$1
fi
mkdir -p "../log/${dte}"
echo $(pwd)

nohup /usr/bin/python hdfwriter.py SH L2 $dte 1>"../log/${dte}/hdfwriter_SH_L2_stdout.log" 2>"../log/${dte}/hdfwriter_SH_L2_stderr.log" &
nohup /usr/bin/python hdfwriter.py SZ L2 $dte 1>"../log/${dte}/hdfwriter_SZ_L2_stdout.log" 2>"../log/${dte}/hdfwriter_SZ_L2_stderr.log" &
