source /etc/profile
cd /opt/production/stocktick/bin
dte=$(date +"%Y%m%d")
mkdir -p "../log/${dte}"
echo $(pwd)

handle_exception () {
    if [[ $1 != 0 ]]
    then
	echo "${2} Fail" > "../log/${dte}/error.message"
	ssh 192.168.1.16 'bash -s' < send_exception.sh
	exit -1
    fi
}

echo "start dump SH L1 market data"
/usr/bin/python hdfarchiver.py SH L1 $dte 1>"../log/${dte}/hdfarchiver_SH_L1_stdout.log" 2>"../log/${dte}/hdfarchiver_SH_L1_stderr.log"
handle_exception $? "hdfarchiver SH L1"

echo "start dump SZ L1 market data"
/usr/bin/python hdfarchiver.py SZ L1 $dte 1>"../log/${dte}/hdfarchiver_SZ_L1_stdout.log" 2>"../log/${dte}/hdfarchiver_SZ_L1_stderr.log" 
handle_exception $? "hdfarchiver SZ L1"

echo "generate SH L1 check report"
/usr/bin/python hdfcheck.py SH L1 $dte 1>"../log/${dte}/hdfcheck_SH_L1_stdout.log" 2>"../log/${dte}/hdfcheck_SH_L1_stderr.log" 
handle_exception $? "hdfcheck SH L1"

echo "generate SZ L1 check report"
/usr/bin/python hdfcheck.py SZ L1 $dte 1>"../log/${dte}/hdfcheck_SZ_L1_stdout.log" 2>"../log/${dte}/hdfcheck_SZ_L1_stderr.log" 
handle_exception $? "hdfcheck SZ L1"

echo "send report email"
ssh 192.168.1.16 'bash -s' < send_report.sh
handle_exception $? "send report"

#echo "start download SH L2 market data"
#/usr/bin/python hdfwriter.py SH L2 $dte 1 1>"../log/${dte}/hdfwriter_SH_L2_stdout.log" 2>"../log/${dte}/hdfwriter_SH_L2_stderr.log"
#handle_exception $? "hdfwriter SH L2 offline"
#
#echo "start download SZ L2 market data"
#/usr/bin/python hdfwriter.py SZ L2 $dte 1 1>"../log/${dte}/hdfwriter_SZ_L2_stdout.log" 2>"../log/${dte}/hdfwriter_SZ_L2_stderr.log"
#handle_exception $? "hdfwriter SZ L2 offline"
#
#echo "start dump SH L2 market data"
#/usr/bin/python hdfarchiver.py SH L2 $dte 1>"../log/${dte}/hdfarchiver_SH_L2_stdout.log" 2>"../log/${dte}/hdfarchiver_SH_L2_stderr.log"
#handle_exception $? "hdfarchiver SH L2 offline"
#
#echo "start dump SZ L2 market data"
#/usr/bin/python hdfarchiver.py SZ L2 $dte 1>"../log/${dte}/hdfarchiver_SZ_L2_stdout.log" 2>"../log/${dte}/hdfarchiver_SZ_L2_stderr.log" 
#handle_exception $? "hdfarchiver SZ L2 offline"

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
