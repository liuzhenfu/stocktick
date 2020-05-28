source /etc/profile
export LD_LIBRARY_PATH=LD_LIBRARY_PATH:/usr/local/lib
cd /datas/production/HHTICK_C/bin/
dte=$(date +"%Y%m%d")
if [ $# == "1" ];then
    dte=$1
fi
echo $(pwd)

./HHTick ../config/config_204_SH.xml $dte 1>"../log/SH_${dte}.log" 2>&1 &
./HHTick ../config/config_204_SZ.xml $dte 1>"../log/SZ_${dte}.log" 2>&1 &