source /etc/profile
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/instantclient_12_1
cd /datas/share/stockdata/L2data/pyscripts/
/usr/local/bin/python getL2.py > log.txt 2>&1