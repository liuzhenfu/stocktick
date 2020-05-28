# -*- coding: utf-8 -*- #
import datetime, os
import pdb,sys
from check_l2 import check, check_c
import pexpect
from sendl2 import send_l2_data

host = '192.168.1.216'
user = 'operation'
passwd = 'op@2016'

# example : scp_get('/datas/a.txt', './')
def scp_get(remote_path, local_path):
    try:
        cmd = 'scp ' + user + '@' + host + ':'
        child = pexpect.spawn(cmd + remote_path + ' ' + local_path)

        index = child.expect(['(?i)password', pexpect.EOF, pexpect.TIMEOUT])
        if (index != 0):
            print('scp connect failed')
            child.close(force=True)
            return
        child.sendline(passwd)
        index = child.expect(['%', 'try again'])
        if index == 1:
            print('passwd error')
            return
        print('scp start...')
        while True:
            process = child.read(150)
            print (process)
            if process.find('100%') != -1:
                print 'scp done'
                break
        return 0
    except Exception,e:
        print 'scp_get {} failed, reason: {}'.format(remote_path, e)
        return -1

def down_load_l2(dte):
    l2_file_names = ['/opt/production/stocktick/L2data/SH/HHTICK_{}.dat'.format(dte),
                     '/opt/production/stocktick/L2data/SZ/HHTICK_{}.dat'.format(dte)]

    scp_get('/opt/production/stocktick/L2data/SZ/HHTICK_{}.dat'.format(dte), '../SZ_N/')
    scp_get('/opt/production/stocktick/L2data/SH/HHTICK_{}.dat'.format(dte), '../SH_N/')
    
    #check(dte)

if __name__ == '__main__':
    dte = int(datetime.datetime.today().strftime("%Y%m%d"))
    if len(sys.argv) > 1:
        dtes = sys.argv[1:]
        for dte in dtes:
            down_load_l2(dte)
        for dte in dtes:
            check_c(dte)
            send_l2_data(dte)
    else :
        down_load_l2(dte)
        check_c(dte)
        send_l2_data(dte)
    
    #dtes = [20170118,20170119,20170120,20170123,20170124, 20180126] 
    #for dte in dtes:
    #    down_load_l2(dte)
    #
    #for dte in dtes:
    #    check(dte)
    
    

