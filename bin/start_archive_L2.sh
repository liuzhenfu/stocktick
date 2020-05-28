source /etc/profile
cd /datas/production/stocktick/bin
dte=$(date +"%Y%m%d")
if [ $# == "1" ];then
    dte=$1
fi
mkdir -p "../log/${dte}"
echo $(pwd)

handle_exception () {
    if [[ $1 != 0 ]]
    then
	echo "${2} Fail" > "../log/${dte}/error.message"
	send_exception.sh ${dte}
	exit -1
    fi
}

echo "start download SH L2 market data"
/usr/bin/python hdfwriter.py SH L2 $dte 1 1>"../log/${dte}/hdfwriter_SH_L2_stdout.log" 2>"../log/${dte}/hdfwriter_SH_L2_stderr.log"

echo "start download SZ L2 market data"
/usr/bin/python hdfwriter.py SZ L2 $dte 1 1>"../log/${dte}/hdfwriter_SZ_L2_stdout.log" 2>"../log/${dte}/hdfwriter_SZ_L2_stderr.log"


echo "start dump SH L2 market data"
/usr/bin/python hdfarchiver.py SH L2 $dte 1>"../log/${dte}/hdfarchiver_SH_L2_stdout.log" 2>"../log/${dte}/hdfarchiver_SH_L2_stderr.log"

echo "start dump SZ L2 market data"
/usr/bin/python hdfarchiver.py SZ L2 $dte 1>"../log/${dte}/hdfarchiver_SZ_L2_stdout.log" 2>"../log/${dte}/hdfarchiver_SZ_L2_stderr.log" 

# echo "generate SH L2 check report"
# /usr/bin/python hdfcheck.py SH L2 $dte 1>"../log/${dte}/hdfcheck_SH_L2_stdout.log" 2>"../log/${dte}/hdfcheck_SH_L2_stderr.log" 
# handle_exception $? "hdfcheck SH L2 offline"

# echo "generate SZ L2 check report"
# /usr/bin/python hdfcheck.py SZ L2 $dte 1>"../log/${dte}/hdfcheck_SZ_L2_stdout.log" 2>"../log/${dte}/hdfcheck_SZ_L2_stderr.log" 
# handle_exception $? "hdfcheck SZ L2"

# echo "send report email"
# ssh 192.168.1.16 'bash -s' < send_report.sh
# handle_exception $? "send report offline"

echo "all done."
