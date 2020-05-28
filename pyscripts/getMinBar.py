# -*- coding: utf-8 -*- #
import datetime, os
import pdb,sys
import pexpect
import time
from email.MIMEMultipart import  MIMEMultipart
from email.MIMEText import MIMEText
import smtplib
import pandas as pd 
import shutil


server = 'smtp.qiye.163.com'
user = 'operation@alpha2fund.com'
passwd = 'tms@2016'
send_to = ['liuzhenfu@alpha2fund.com','wangchao@alpha2fund.com','lvjieyong@alpha2fund.com']

def send_email(send_to, subject, content, fmt = 'plain'):
    try:
        COMMASPACE = ', '
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['To'] = COMMASPACE.join(send_to)
        msg.attach(MIMEText(content, fmt, 'utf-8'))

        smtp = smtplib.SMTP()
        smtp.connect(server)
        smtp.login(user, passwd)
        smtp.sendmail(user, send_to, msg.as_string())
        smtp.close()
        print "send success."
    except Exception, e:
        print "send fail.", e
        
def ssh_login(host, user, passwd):
    cmd = 'ssh {}@{}'.format(user, host)
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

# example : scp_get('/datas/a.txt', './')
def scp_get(src_path, dst_path, passwd):
    try:
        cmd = 'scp '
        child = pexpect.spawn(cmd + src_path + ' ' + dst_path)

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
        print 'scp_get {} failed, reason: {}'.format(src_path, e)
        send_email(send_to, u'bar数据上传失败', u'scp_get {} failed, reason: {}'.format(src_path, e))
        return -1
 
def getBarData(dte):
    try:
        now = int(datetime.datetime.now().strftime('%H%M%S'))
        host = '192.168.1.216'
        user = 'operation'
        passwd = 'op@2016'
        remote_path = '/opt/production/stocktick/bar_data/{}/{}/{}.csv'
        local_path = '../BarData/Min5/{}/{}/'
        prefix = user+'@'+host+':'
        if now > 113000 and now < 150000:
            scp_get(prefix+remote_path.format('halfday', 'SH', str(dte)+'113000'), local_path.format('halfday', 'SH'), passwd)
            scp_get(prefix+remote_path.format('halfday', 'SZ', str(dte)+'113000'), local_path.format('halfday', 'SZ'), passwd)
            scp_get(prefix+remote_path.format('halfday', 'SHI', str(dte)+'113000'), local_path.format('halfday', 'SHI'), passwd)
            scp_get(prefix+remote_path.format('halfday', 'SZI', str(dte)+'113000'), local_path.format('halfday', 'SZI'), passwd)
        if now > 150000:
            scp_get(prefix+remote_path.format('allday', 'SH', str(dte)+'150000'), local_path.format('allday', 'SH'), passwd)
            scp_get(prefix+remote_path.format('allday', 'SZ', str(dte)+'150000'), local_path.format('allday', 'SZ'), passwd)
            scp_get(prefix+remote_path.format('allday', 'SHI', str(dte)+'150000'), local_path.format('allday', 'SHI'), passwd)
            scp_get(prefix+remote_path.format('allday', 'SZI', str(dte)+'150000'), local_path.format('allday', 'SZI'), passwd)
    except Exception,e:
        print 'getBarData failed, reason: {}'.format(e)
        send_email(send_to, u'bar数据上传失败', u'getBarData failed, reason: {}'.format(e))
        return -1

def mergeData(dte):
    root_dir = '../BarData/Min5/{}/'
    now = int(datetime.datetime.now().strftime('%H%M%S'))
    merge_f, sz_f, sh_f, szi_f, shi_f = None, None, None, None, None
    if now > 113000 and now < 150000:        
        root_dir = root_dir.format('halfday')
        merge_f = open('{}/PV/{}.csv'.format(root_dir, dte),'w+')
        sz_f = open('{}/SZ/{}.csv'.format(root_dir, str(dte)+'113000'), 'r')
        sh_f = open('{}/SH/{}.csv'.format(root_dir, str(dte)+'113000'), 'r')
        szi_f = open('{}/SZI/{}.csv'.format(root_dir, str(dte)+'113000'), 'r')
        shi_f = open('{}/SHI/{}.csv'.format(root_dir, str(dte)+'113000'), 'r')
    if now > 150000:       
        root_dir = root_dir.format('allday')
        merge_f = open('{}/PV/{}.csv'.format(root_dir, dte),'w+')
        sz_f = open('{}/SZ/{}.csv'.format(root_dir, str(dte)+'150000'), 'r')
        sh_f = open('{}/SH/{}.csv'.format(root_dir, str(dte)+'150000'), 'r')
        szi_f = open('{}/SZI/{}.csv'.format(root_dir, str(dte)+'150000'), 'r')
        shi_f = open('{}/SHI/{}.csv'.format(root_dir, str(dte)+'150000'), 'r')
    if merge_f and sz_f and sh_f and szi_f and shi_f:
        merge_f.write("date,time,symbol,high,low,open,close,volume,amount,twap,vwap,last_ask,last_bid,avg_ask,avg_bid,avg_askvol1,avg_askvol,avg_bidvol1,avg_bidvol\n")

        for line in sh_f.readlines():
            if line.find('date') == -1 and line != "":
                merge_f.write(line)
        for line in sz_f.readlines():
            if line.find('date') == -1 and line != "":
                merge_f.write(line)
        for line in shi_f.readlines():
            if line.find('date') == -1 and line != "":
                merge_f.write(line)
        for line in szi_f.readlines():
            if line.find('date') == -1 and line != "":
                merge_f.write(line)
    else :
        print 'files not complete'
        raise RuntimeError('files not complete')
    merge_f.close()
    # group by time 
    df = pd.read_csv('{}/PV/{}.csv'.format(root_dir, dte))
    dirname = '{}/PV/{}/'.format(root_dir, dte)
    os.mkdir(dirname)
    group = df.groupby('time')
    for name, g in group:
        g.to_csv('{}/PV/{}/{}.csv'.format(root_dir, dte, name.replace(':','')), index=False)
    zip_file = shutil.make_archive(dirname,'zip',dirname)
    shutil.rmtree(dirname)
    
def sendBarData(dte):
    try:
        now = int(datetime.datetime.now().strftime('%H%M%S'))
        host = '118.190.62.49'
        user = 'tuserftp'
        passwd = 'tuser2016'
        prefix = user+'@'+host+':'
        
        remote_path = '/opt/data/ftpdir/tusershare/Min5/PV/{}/'
        local_path = '../BarData/Min5/{}/{}/{}.zip'
        if now > 113000 and now < 150000:
            scp_get(local_path.format('halfday', 'PV', str(dte)), prefix+remote_path.format(dte), passwd)
            #scp_get(local_path.format('halfday', 'SZ', str(dte)+'113000'), prefix+remote_path.format('halfday', 'SZ', dte), passwd)
        if now > 150000:
            scp_get(local_path.format('allday', 'PV', str(dte)), prefix+remote_path.format(dte), passwd)
            #scp_get(local_path.format('allday', 'SZ', str(dte)+'150000'), prefix+remote_path.format('allday', 'SZ', dte), passwd)
    except Exception,e:
        print 'sendBarData failed, reason: {}'.format(e)
        send_email(send_to, u'bar数据上传失败', u'sendBarData failed, reason: {}'.format(e))
        return -1
        
def createRemotPath(dte):
    host = '118.190.62.49'
    user = 'tuserftp'
    passwd = 'tuser2016'
    handler = ssh_login(host, user, passwd)
    cmd = 'cd /opt/data/ftpdir/tusershare/Min5/PV/'
    now = int(datetime.datetime.now().strftime('%H%M%S'))

    handler.sendline(cmd)
    print handler.readline()

    #crt_cmd = 'mkdir {}'.format(dte)
    #handler.sendline(crt_cmd)
    crt_cmd = 'mkdir {}'.format(dte)
    handler.sendline(crt_cmd)
    print handler.readline()
    time.sleep(1)
def unzip_file(dte):
    host = '118.190.62.49'
    user = 'tuserftp'
    passwd = 'tuser2016'
    handler = ssh_login(host, user, passwd)
    cmd = 'cd /opt/data/ftpdir/tusershare/Min5/PV/{}/'
    now = int(datetime.datetime.now().strftime('%H%M%S'))
    
    handler.sendline(cmd.format(dte))
    print handler.readline()
    print 'unzip file'
    unzip_cmd = ' unzip -o {}.zip '.format(dte)
    handler.sendline(unzip_cmd)
    print handler.readline()
    time.sleep(2)
    del_cmd = 'rm {}.zip'.format(dte)
    handler.sendline(del_cmd)
    print handler.readline()
    time.sleep(1)
    
def run(dte):
    getBarData(dte)
    mergeData(dte)
    createRemotPath(dte)
    sendBarData(dte)
    unzip_file(dte)
    
if __name__ == '__main__':
    dte = int(datetime.datetime.today().strftime("%Y%m%d"))
    if len(sys.argv) > 1:
        dtes = sys.argv[1:]
        for dte in dtes:
            run(dte)
    else :
        run(dte)
    send_email(send_to, u'bar数据上传成功', '')
    
