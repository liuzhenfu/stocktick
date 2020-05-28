# -*- coding: utf-8 -*- #
import os
import pdb
import sys
import datetime
from pyscp import scp_get

remote_path = '/datas/bsim/modules/DataGenerator/StkBars.{}/testdata/csv/{}'
local_path = '/opt/production/stocktick/bar_data/{}/{}/'
host = '172.18.94.223'
user = 'root'
passwd = '123456'

prefix = user+'@'+host+':'
def getBarData(dte):
    now = int(datetime.datetime.now().strftime('%H%M%S'))
    if int(now) > 113000 and int(now) < 150000:
        # half day
        scp_get(prefix+remote_path.format('SH',str(dte)+'113000.csv'), local_path.format('halfday','SH'), passwd)
        scp_get(prefix+remote_path.format('SZ',str(dte)+'113000.csv'), local_path.format('halfday','SZ'), passwd)
        scp_get(prefix+remote_path.format('SH.index',str(dte)+'113000.csv'), local_path.format('halfday','SHI'), passwd)
        scp_get(prefix+remote_path.format('SZ.index',str(dte)+'113000.csv'), local_path.format('halfday','SZI'), passwd)
    if int(now) > 150000:
        scp_get(prefix+remote_path.format('SH',str(dte)+'150000.csv'), local_path.format('allday','SH'), passwd)
        scp_get(prefix+remote_path.format('SZ',str(dte)+'150000.csv'), local_path.format('allday','SZ'), passwd)
        scp_get(prefix+remote_path.format('SH.index',str(dte)+'150000.csv'), local_path.format('allday','SHI'), passwd)
        scp_get(prefix+remote_path.format('SZ.index',str(dte)+'150000.csv'), local_path.format('allday','SZI'), passwd)
        
if __name__ == '__main__':
    dte = datetime.datetime.today().strftime('%Y%m%d')
    getBarData(dte)

