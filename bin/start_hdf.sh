source /etc/profile
cd /opt/production/stocktick/bin
dte=$(date +"%Y%m%d")
mkdir -p "../log/${dte}"
echo $(pwd)

nohup /usr/bin/python hdfwriter.py SH L1 $dte 1>"../log/${dte}/hdfwriter_SH_L1_stdout.log" 2>"../log/${dte}/hdfwriter_SH_L1_stderr.log" &
nohup /usr/bin/python hdfwriter.py SZ L1 $dte 1>"../log/${dte}/hdfwriter_SZ_L1_stdout.log" 2>"../log/${dte}/hdfwriter_SZ_L1_stderr.log" &
