# -*- coding: utf-8 -*- #
import datetime, os, time
import pdb,sys

import pexpect

host = '101.96.129.42'
user = 'windhh'
passwd = '123456'
port = 53450

def ssh_login(host, user, passwd):
    cmd = 'ssh -p {} {}@{}'.format(port,user, host)
    print(cmd)
    child = pexpect.spawn(cmd)
    index = child.expect(['(?i)password', pexpect.EOF, pexpect.TIMEOUT])
    if index != 0:
        print ('ssh connect failed')
        child.close(force=True)
        return None
    child.sendline(passwd)
    index = child.expect([user, 'try again'])
    if index == 1:
        print('passwd error')
        return None
    print('ssh login success')
    return child
    
# example : scp_get('/datas/a.txt', './') scp -C -P 53450 HHTICK_20180126.dat windhh@101.96.129.42:/media/dbstore/data/windHHData/2018/SH/
def scp_put(src_path, dst_path):
    try:
        cmd = 'scp -C -P {} '.format(port)
        print (cmd + src_path + ' ' + '{}@{}:{}'.format(port, user, host,dst_path))
        child = pexpect.spawn(cmd + src_path + ' ' + '-P {} {}@{}:{}'.format(port, user, host,dst_path))

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
        print 'scp_get {} failed, reason: {}'.format(dst_path, e)
        return -1

def create_remote_path(dte):
    handler = ssh_login(host, user, passwd)
    cmd = 'cd /media/dbstore/data/windHHData/2018/'
    handler.sendline(cmd)
    print handler.readline()

    crt_cmd = 'mkdir {}'.format(dte)
    handler.sendline(crt_cmd)
    crt_cmd = 'mkdir {}/SH/'.format(dte)
    handler.sendline(crt_cmd)
    crt_cmd = 'mkdir {}/SZ/'.format(dte)
    handler.sendline(crt_cmd)
    print handler.readline()
    time.sleep(1)
    
def send_l2_data(dte):
    remote_path = '/media/dbstore/data/windHHData/2018/{}/'.format(dte)
    local_path = '/datas/share/stockdata/L2data/'
    create_remote_path(dte)
    scp_put("{}SH_N/HHTICK_{}.dat".format(local_path, dte), remote_path+'SH/')
    scp_put("{}SZ_N/HHTICK_{}.dat".format(local_path, dte), remote_path+'SZ/')
    
if __name__ == '__main__':
    dte = int(datetime.datetime.today().strftime("%Y%m%d"))
    if len(sys.argv) > 1:
        dte = int(sys.argv[1])
    for dte in [20180102,20180103,20180104,20180105,20180108,20180109,20180110,20180111,20180112,20180115,20180116,20180117,20180118,20180119,20180122,20180123,20180124,20180125]:
        send_l2_data(dte)
    